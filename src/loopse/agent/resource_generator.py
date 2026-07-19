"""
ResourceGeneratorAgent：学习资源生成代理
支持五种资源类型：知识文档（doc）、练习题（exercise）、代码示例（code）、
思维导图（mindmap）、视频脚本（script）
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.llm_client import llm_client
from ..db.repositories import ResourceRepository
from .cognitive_engine import AwaitableDict, CognitiveAgentMixin

logger = logging.getLogger(__name__)

# ── RL 方向1: LinUCB 上下文赌博机（软依赖，失败时优雅降级到规则策略）──
try:
    from ..rl.contextual_bandit import get_bandit as _get_bandit
    _RL_BANDIT_AVAILABLE = True
    logger.debug("[ResourceGen] LinUCB bandit 可用")
except Exception:
    _RL_BANDIT_AVAILABLE = False
    logger.debug("[ResourceGen] LinUCB bandit 不可用，使用规则策略")

_PROMPT_DIR = Path("config/prompts/resource_generator")


def _load_prompt(name: str) -> str:
    p = _PROMPT_DIR / name
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("[ResourceGen] prompt 文件缺失: %s", p)
        return ""


class ResourceGeneratorAgent(CognitiveAgentMixin):
    """
    学习资源生成代理，支持五类资源：
    - doc：知识点总结文档（Markdown 格式）
    - exercise：练习题（含答案与解析）
    - code：代码/协议模拟示例
    - mindmap：思维导图（Mermaid 语法）
    - script：视频脚本（结构化 JSON）
    """

    RESOURCE_TYPES = ("doc", "exercise", "code", "mindmap", "script", "infographic")

    # 认知风格 → 资源类型优先级
    STYLE_PRIORITY = {
        "visual": ["mindmap", "script", "doc"],
        "practical": ["code", "exercise", "doc"],
        "textual": ["doc", "exercise", "mindmap"],
        "analogical": ["doc", "script", "exercise"],
    }

    # 诊断错误类型 → 强制追加资源类型
    ERROR_BOOST = {
        "flow_omission": ["simulator"],
        "layer_misplacement": ["mindmap", "http_encapsulation"],
        "field_misunderstanding": ["exercise"],
        "concept_confusion": ["exercise", "mindmap"],
        "reasoning_breakdown": ["doc", "exercise"],
    }

    def __init__(self):
        self._doc_prompt = _load_prompt("generate_doc.txt")
        self._exercise_prompt = _load_prompt("generate_exercise.txt")
        self._code_prompt = _load_prompt("generate_code.txt")
        self._mindmap_prompt = _load_prompt("generate_mindmap.txt")
        self._script_prompt = _load_prompt("generate_script.txt")
        self._infographic_prompt = _load_prompt("generate_infographic.txt")

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def generate(
        self,
        resource_type: str,
        knowledge_point: str,
        context_docs: Optional[List[Dict]] = None,
        difficulty: int = 3,
    ) -> Dict[str, Any]:
        """
        生成指定类型的学习资源。

        Args:
            resource_type: "doc" / "exercise" / "code" / "mindmap" / "script"
            knowledge_point: 目标知识点名称（如 "TCP三次握手"）
            context_docs: 检索到的参考文档片段
            difficulty: 难度（1-5）

        Returns:
            {
                "resource_id": str,
                "resource_type": str,
                "knowledge_point": str,
                "title": str,
                "content": str,
                "metadata": {...},
                "created_at": str,
            }
        """
        if resource_type not in self.RESOURCE_TYPES:
            raise ValueError(f"不支持的资源类型: {resource_type}，可选: {self.RESOURCE_TYPES}")

        logger.info("[ResourceGen] 生成开始 | type=%s | kp=%s | difficulty=%d", resource_type, knowledge_point, difficulty)
        _t0 = time.time()

        trace = self.make_trace(f"generate:{resource_type}:{knowledge_point}")
        trace.add_step(
            "plan",
            f"resource_type={resource_type}, difficulty={difficulty}",
            "select_prompt_and_context",
            0.85,
        )

        generators = {
            "doc": self._generate_doc,
            "exercise": self._generate_exercise,
            "code": self._generate_code,
            "mindmap": self._generate_mindmap,
            "script": self._generate_script,
            "infographic": self._generate_infographic,
        }

        try:
            resource = generators[resource_type](knowledge_point, context_docs, difficulty)
        except Exception as exc:
            logger.error("[ResourceGen] 生成失败 | type=%s | error=%s", resource_type, exc)
            resource = self._build_resource(
                resource_type,
                knowledge_point,
                f"【{resource_type}】{knowledge_point}（生成失败，已使用备选内容）",
                self._fallback_content(resource_type, knowledge_point),
                {"difficulty": difficulty, "fallback": True},
            )

        checks = {
            "has_content": len(resource.get("content", "")) >= 20,
            "has_title": bool(resource.get("title")),
            "type_matched": resource.get("resource_type") == resource_type,
        }
        reflection = self.reflect(trace, checks)
        resource["metadata"]["agent_trace"] = trace.to_dict()
        resource["quality_score"] = round(0.6 + 0.4 * reflection["confidence"], 3)
        try:
            ResourceRepository.save(resource)
        except Exception as exc:
            logger.warning("[ResourceGen] resource persistence skipped: %s", exc)
        logger.info(
            "[ResourceGen] 生成完成 | type=%s | 耗时=%.0fms | quality=%.2f",
            resource_type, (time.time() - _t0) * 1000, resource.get("quality_score", 0),
        )
        return AwaitableDict(resource)

    def generate_all(
        self,
        knowledge_point: str,
        context_docs: Optional[List[Dict]] = None,
        difficulty: int = 3,
        resource_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        一次性生成多类学习资源。

        Args:
            knowledge_point: 目标知识点名称
            context_docs: 检索到的参考文档片段
            difficulty: 难度（1-5）
            resource_types: 指定生成的资源类型列表，默认全部5类

        Returns:
            {
                "knowledge_point": str,
                "docs": ...,
                "exercise": ...,
                "code": ...,
                "mindmap": ...,
                "script": ...,
                "total_resources": int,
                "generated_at": str,
            }
        """
        types_to_gen = resource_types or list(self.RESOURCE_TYPES)
        logger.info("[ResourceGen] generate_all 开始 | types=%d | kp=%s", len(types_to_gen), knowledge_point)
        _t0 = time.time()
        trace = self.make_trace(f"generate_all:{knowledge_point}")

        resources = {}
        for res_type in types_to_gen:
            if res_type not in self.RESOURCE_TYPES:
                continue
            try:
                resources[res_type] = self.generate(res_type, knowledge_point, context_docs, difficulty)
            except Exception as exc:
                import traceback
                logger.warning("[ResourceGen] 生成 %s 资源失败: %s", res_type, exc)
                logger.debug("[ResourceGen] 完整堆栈:\n%s", traceback.format_exc())
                resources[res_type] = None

        trace.add_step(
            "all_generated",
            f"types={list(resources.keys())}, success={sum(1 for v in resources.values() if v is not None)}",
            "complete",
            0.85,
        )

        result: Dict[str, Any] = {
            "knowledge_point": knowledge_point,
            "total_resources": sum(1 for v in resources.values() if v is not None),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        for res_type in self.RESOURCE_TYPES:
            result[res_type] = resources.get(res_type)

        logger.info(
            "[ResourceGen] generate_all 完成 | 耗时=%.0fms | success=%d/%d",
            (time.time() - _t0) * 1000,
            result.get("total_resources", 0),
            len(types_to_gen),
        )
        return AwaitableDict(result)

    # ------------------------------------------------------------------
    # 诊断驱动的资源推荐入口（激活 _select_resource_types 闭环）
    # ------------------------------------------------------------------

    def generate_from_diagnosis(
        self,
        knowledge_point: str,
        diagnosis_result: Dict[str, Any],
        profile: Optional[Dict] = None,
        context_docs: Optional[List[Dict]] = None,
        difficulty: int = 3,
        max_types: int = 3,
    ) -> Dict[str, Any]:
        """根据诊断结果自动选择资源类型并生成。

        主流程：
        1. 通过 _select_resource_types 融合认知风格和诊断错误类型确定资源类型列表
        2. 优先使用 diagnosis_result.recommended_interventions 中的策略类型
        3. 生成对应资源并返回结构化结果

        Args:
            knowledge_point: 目标知识点名称
            diagnosis_result: DiagnosisAgent.diagnose() 返回的诊断结果字典
            profile: 学生画像（可选）
            context_docs: 检索参考文档（可选）
            difficulty: 难度
            max_types: 最多生成的资源类型数量

        Returns:
            {
                "knowledge_point": str,
                "diagnosis_driven": True,
                "selected_types": [...],
                "resources": {type: resource_dict},
                "strategy_reason": str,
                "total_resources": int,
                "generated_at": str,
            }
        """
        logger.info(
            "[ResourceGen] generate_from_diagnosis | kp=%s | error_type=%s | pattern=%s",
            knowledge_point,
            diagnosis_result.get("error_type", "unknown"),
            diagnosis_result.get("pattern", "none"),
        )
        _t0 = time.time()

        # 优先使用 recommended_interventions（来自 ACU repair_strategies）
        recommended = diagnosis_result.get("recommended_interventions", [])
        valid_recommended = [r for r in recommended if r in self.RESOURCE_TYPES]

        if valid_recommended:
            selected_types = list(dict.fromkeys(valid_recommended))[:max_types]
            strategy_reason = (
                f"诊断建议使用 {selected_types} 资源类型修复"
                f"『{diagnosis_result.get('error_type', '')}』错误模式。"
            )
        elif _RL_BANDIT_AVAILABLE and profile:
            # RL方向1: LinUCB 上下文赌博机自适应选择资源类型
            try:
                user_id = profile.get("user_id", "global")
                bandit = _get_bandit(user_id)
                context = bandit.build_context(profile, diagnosis_result)
                selected_types, ucb_scores = bandit.select_arms(context, max_types)
                strategy_reason = (
                    f"[LinUCB-RL] 基于认知画像自适应推荐 {selected_types}；"
                    f"UCB得分={ucb_scores}（α={bandit.alpha:.2f}，"
                    f"已学习{bandit._total}次）。"
                )
                logger.info("[ResourceGen] LinUCB选臂 types=%s ucb=%s", selected_types, ucb_scores)
            except Exception as _rl_exc:
                logger.warning("[ResourceGen] LinUCB失败，降级: %s", _rl_exc)
                selected_types = self._select_resource_types(profile, diagnosis_result)[:max_types]
                strategy_reason = f"规则策略（LinUCB降级）: {diagnosis_result.get('error_type', '')}"
        else:
            # 回退到画像+诊断驱动的规则策略
            selected_types = self._select_resource_types(profile, diagnosis_result)[:max_types]
            strategy_reason = (
                f"根据认知风格 {profile.get('cognitive_style', 'textual') if profile else 'textual'} "
                f"和错误类型 {diagnosis_result.get('error_type', '')} 选择资源类型。"
            )

        # 确保至少有 doc
        if "doc" not in selected_types:
            selected_types = ["doc"] + selected_types[: max_types - 1]

        resources: Dict[str, Any] = {}
        for res_type in selected_types:
            if res_type not in self.RESOURCE_TYPES:
                continue
            try:
                resources[res_type] = self.generate(
                    res_type, knowledge_point, context_docs, difficulty
                )
            except Exception as exc:
                logger.warning("[ResourceGen] generate_from_diagnosis %s 失败: %s", res_type, exc)
                resources[res_type] = None

        result = {
            "knowledge_point": knowledge_point,
            "diagnosis_driven": True,
            "selected_types": selected_types,
            "strategy_reason": strategy_reason,
            "misconception_id": diagnosis_result.get("misconception_id"),
            "acu_ids": diagnosis_result.get("acu_ids", []),
            "resources": resources,
            "total_resources": sum(1 for v in resources.values() if v is not None),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(
            "[ResourceGen] generate_from_diagnosis 完成 | 耗时=%.0fms | types=%s | success=%d",
            (time.time() - _t0) * 1000,
            selected_types,
            result["total_resources"],
        )
        return AwaitableDict(result)

    # ------------------------------------------------------------------
    # 画像驱动的资源推送策略
    # ------------------------------------------------------------------

    def _select_resource_types(
        self,
        profile: Optional[Dict] = None,
        diagnosis: Optional[Dict] = None,
    ) -> List[str]:
        """根据学生画像和诊断结果选择推荐资源类型。

        推送规则：
        - 认知风格 = visual → 优先 mindmap + script + doc
        - 认知风格 = practical → 优先 code + exercise + doc
        - 认知风格 = textual → 优先 doc + exercise + mindmap
        - 认知风格 = analogical → 优先 doc + script + exercise

        叠加诊断结果：
        - 有 flow_omission 错误 → 强制追加 simulator 推荐
        - 有 layer_misplacement 错误 → 强制追加 mindmap + http_encapsulation 仿真
        - 有 field_misunderstanding 错误 → 强制追加 exercise（报文分析题）

        Returns:
            推荐资源类型列表
        """
        cognitive_style = "textual"
        if profile:
            cognitive_style = profile.get("cognitive_style", "textual")

        # 基于认知风格选择基础类型
        selected = list(self.STYLE_PRIORITY.get(cognitive_style, ["doc", "exercise", "code"]))

        # 叠加诊断结果
        if diagnosis:
            error_type = diagnosis.get("error_type", "")
            pattern = diagnosis.get("pattern", "")

            # 检查已知错误类型
            for err_key, boost_types in self.ERROR_BOOST.items():
                if err_key in str(error_type) or err_key in str(pattern):
                    for bt in boost_types:
                        if bt not in selected and bt in self.RESOURCE_TYPES:
                            selected.append(bt)

        # 确保至少有 doc
        if "doc" not in selected:
            selected.insert(0, "doc")

        return selected

    # ------------------------------------------------------------------
    # 类型1：知识文档
    # ------------------------------------------------------------------

    def _generate_doc(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        doc_prompt = getattr(self, "_doc_prompt", "")
        if doc_prompt:
            prompt = doc_prompt.format(
                knowledge_point=knowledge_point,
                context_docs=context,
                difficulty=difficulty,
                cognitive_style="textual",
                weakness_summary="",
                reference_content=context,
                source_chapter="第5章 TCP/UDP协议",
            )
        else:
            prompt = (
                f"请为计算机网络课程的「{knowledge_point}」知识点，"
                f"生成一份适合难度{difficulty}级学生的学习文档。\n"
                f"参考材料：{context[:500]}\n"
                "要求：结构清晰，包含定义、核心原理、要点总结，Markdown格式输出。"
            )

        content = self._chat(prompt, max_tokens=1000)
        title = f"【知识文档】{knowledge_point}"

        return self._build_resource("doc", knowledge_point, title, content, {"difficulty": difficulty})

    # ------------------------------------------------------------------
    # 类型2：练习题
    # ------------------------------------------------------------------

    def _generate_exercise(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        exercise_prompt = getattr(self, "_exercise_prompt", "")
        if exercise_prompt:
            prompt = exercise_prompt
            prompt = prompt.replace("{knowledge_point}", knowledge_point)
            prompt = prompt.replace("{context_docs}", context)
            prompt = prompt.replace("{difficulty}", str(difficulty))
            prompt = prompt.replace("{error_type}", "conceptual")
            prompt = prompt.replace("{exercise_type}", "choice")
            prompt = prompt.replace("{reference_content}", context)
        else:
            prompt = (
                f"请为「{knowledge_point}」生成3道练习题（难度{difficulty}级）。\n"
                f"参考材料：{context[:500]}\n"
                "要求：包含选择题1道、判断题1道、简答题1道，每题附标准答案和解析。"
            )

        content = self._chat(prompt, max_tokens=800)
        title = f"【练习题】{knowledge_point}"

        return self._build_resource("exercise", knowledge_point, title, content, {
            "difficulty": difficulty,
            "question_count": 3,
        })

    # ------------------------------------------------------------------
    # 类型3：代码/协议示例
    # ------------------------------------------------------------------

    def _generate_code(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        code_prompt = getattr(self, "_code_prompt", "")
        if code_prompt:
            prompt = code_prompt
            prompt = prompt.replace("{knowledge_point}", knowledge_point)
            prompt = prompt.replace("{context_docs}", context)
            prompt = prompt.replace("{difficulty}", str(difficulty))
            prompt = prompt.replace("{reference_content}", context)
        else:
            prompt = (
                f"请为「{knowledge_point}」生成一个 Python 代码示例，模拟或演示该协议/概念的核心逻辑。\n"
                f"参考材料：{context[:300]}\n"
                "要求：代码可运行，包含详细注释，展示关键状态变化。"
            )

        content = self._chat(prompt, max_tokens=800)
        title = f"【代码示例】{knowledge_point}"

        return self._build_resource("code", knowledge_point, title, content, {
            "language": "python",
            "difficulty": difficulty,
        })

    # ------------------------------------------------------------------
    # 类型4：思维导图（Mermaid）
    # ------------------------------------------------------------------

    def _generate_mindmap(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        mindmap_prompt = getattr(self, "_mindmap_prompt", "")
        if mindmap_prompt:
            prompt = mindmap_prompt.format(
                knowledge_point=knowledge_point,
                reference_content=context,
                context_docs=context,
                difficulty=difficulty,
            )
        else:
            prompt = (
                f"请为计算机网络知识点「{knowledge_point}」生成 Mermaid 思维导图。\n"
                f"参考材料：{context[:300]}\n"
                "要求：中心节点为知识点名称，标注2-3个常见误解分支，不超过3层。"
            )

        content = self._chat(prompt, max_tokens=600)
        title = f"【思维导图】{knowledge_point}"

        return self._build_resource("mindmap", knowledge_point, title, content, {
            "difficulty": difficulty,
            "format": "mermaid",
        })

    # ------------------------------------------------------------------
    # 类型5：视频脚本
    # ------------------------------------------------------------------

    def _generate_script(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        script_prompt = getattr(self, "_script_prompt", "")
        if script_prompt:
            prompt = script_prompt.format(
                knowledge_point=knowledge_point,
                reference_content=context,
                context_docs=context,
                difficulty=difficulty,
            )
        else:
            prompt = (
                f"请为计算机网络知识点「{knowledge_point}」生成60-90秒的讲解视频脚本。\n"
                f"参考材料：{context[:300]}\n"
                "要求：4-6个场景，每场景含场景描述、旁白文案、视觉备注。返回JSON。"
            )

        content = self._chat(prompt, max_tokens=800)
        title = f"【视频脚本】{knowledge_point}"

        return self._build_resource("script", knowledge_point, title, content, {
            "difficulty": difficulty,
            "format": "json",
            "estimated_duration": "60-90秒",
        })

    # ------------------------------------------------------------------
    # 类型6：信息图（infographic）
    # ------------------------------------------------------------------

    def _generate_infographic(
        self,
        knowledge_point: str,
        context_docs: Optional[List[Dict]] = None,
        difficulty: int = 3,
    ) -> Dict[str, Any]:
        """Generate a structured infographic JSON card for rendering."""
        context = self._format_context(context_docs)
        if self._infographic_prompt:
            prompt = (
                self._infographic_prompt
                .replace("{knowledge_point}", knowledge_point)
                .replace("{context}", context[:400])
                .replace("{difficulty}", str(difficulty))
            )
        else:
            prompt = (
                f"请为计算机网络知识点「{knowledge_point}」生成一张结构化信息图 JSON。"
                f"参考材料：{context[:300]}"
                "要求：返回 JSON 格式，包含："
                "title(标题), summary(一句话摘要), "
                "key_numbers(关键数字列表,每项包含 value+unit+desc), "
                "comparison(对比表, 包含 header+rows), "
                "timeline(关键流程步骤列表,每项包含 step+desc), "
                "tags(关键标签列表)."
            )

        content = self._chat(prompt, max_tokens=700)
        title = f"【信息图】{knowledge_point}"

        return self._build_resource("infographic", knowledge_point, title, content, {
            "difficulty": difficulty,
            "format": "json",
        })

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _chat(self, prompt: str, max_tokens: int) -> str:  # type: ignore[no-redef]
        client = getattr(self, "llm", llm_client)
        return client.chat(prompt, max_tokens=max_tokens)

    @staticmethod
    def _fallback_content(res_type: str, knowledge_point: str) -> str:
        """JSON 解析失败或 LLM 调用失败时的备选内容。"""
        fallbacks = {
            "doc": f"# {knowledge_point}\n\n## 概述\n{knowledge_point}是计算机网络中的核心概念。\n\n## 关键要点\n- 理解基本定义和原理\n- 掌握协议交互流程\n- 能够分析常见误区\n\n## 总结\n建议结合仿真动画和练习题进一步巩固。",
            "exercise": f"# {knowledge_point} 练习题\n\n## 选择题\n下列关于{knowledge_point}的说法，正确的是？\nA. 选项一\nB. 选项二\nC. 选项三\nD. 选项四\n\n答案：B\n解析：根据{knowledge_point}的定义，B 选项正确。\n\n## 判断题\n{knowledge_point}只涉及单层协议。\n答案：错误\n解析：{knowledge_point}涉及多层协议交互。",
            "code": f"# {knowledge_point} 代码示例\n\n```python\n# 模拟 {knowledge_point} 的核心逻辑\ndef demo():\n    \"\"\"演示{knowledge_point}的关键流程。\"\"\"\n    print('Step 1: 初始化')\n    print('Step 2: 执行核心流程')\n    print('Step 3: 完成')\n    return 'done'\n\nif __name__ == '__main__':\n    demo()\n```",
            "mindmap": f"```mermaid\nmindmap\n  root(({knowledge_point}))\n    定义\n      基本概念\n      核心原理\n    流程\n      步骤1\n      步骤2\n    常见误区\n      误区1\n      误区2\n```",
            "script": '{"scenes": [{"scene": 1, "description": "开场", "narration": "今天我们学习' + knowledge_point + '", "visual": "标题动画"}, {"scene": 2, "description": "核心讲解", "narration": "关键概念解析", "visual": "图表示意"}]}',
            "infographic": '{"title": "' + knowledge_point + '", "summary": "' + knowledge_point + '是计算机网络中的重要概念", "key_numbers": [], "comparison": {"header": ["特性", "说明"], "rows": []}, "timeline": [], "tags": ["' + knowledge_point + '"]}',
        }
        return fallbacks.get(res_type, f"{knowledge_point} 的学习资源（备选内容）")

    @staticmethod
    def _format_context(docs: Optional[List[Dict]]) -> str:
        if not docs:
            return "（无参考文档）"
        snippets = [d.get("document", d.get("text", ""))[:200] for d in docs[:3] if d]
        return "\n".join(filter(None, snippets)) or "（无参考文档）"

    @staticmethod
    def _build_resource(
        res_type: str,
        knowledge_point: str,
        title: str,
        content: str,
        metadata: Dict,
    ) -> Dict[str, Any]:
        return {
            "resource_id": str(uuid.uuid4()),
            "resource_type": res_type,
            "knowledge_point": knowledge_point,
            "title": title,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
