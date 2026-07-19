"""Agent 长期记忆管理器。

跨会话持久化用户记忆，按人格隔离，支持归档与清理。

记忆类型：
- long_term：跨会话关键事实（用户反复提及的概念、纠错历史）
- session_summary：会话结束时的摘要（自动归档）
- preference：用户偏好（学习风格、常见话题等）
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemoryManager:
    """管理用户长期记忆的 CRUD 操作。"""

    # 每个用户+人格最多保留的长期记忆条数
    MAX_MEMORY_PER_PERSONA = 20

    def get_memories(
        self,
        user_id: str,
        persona: str = "general",
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """获取指定用户/人格的记忆列表（按时间倒序）。"""
        try:
            from ..db.repositories import get_db_session
            from ..db.models import MemoryRecord
            with get_db_session() as db:
                q = db.query(MemoryRecord).filter(
                    MemoryRecord.user_id == user_id,
                    MemoryRecord.persona == persona,
                    MemoryRecord.archived_at.is_(None),
                )
                if memory_type:
                    q = q.filter(MemoryRecord.memory_type == memory_type)
                records = q.order_by(MemoryRecord.created_at.desc()).limit(limit).all()
                return [
                    {
                        "id": r.id,
                        "persona": r.persona,
                        "memory_type": r.memory_type,
                        "content": r.content,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                    }
                    for r in records
                ]
        except Exception as exc:
            logger.warning("[Memory] get_memories 失败 user=%s: %s", user_id, exc)
            return []

    def add_memory(
        self,
        user_id: str,
        content: str,
        persona: str = "general",
        memory_type: str = "long_term",
    ) -> str:
        """新增一条记忆，超出上限时自动淘汰最旧记录。"""
        if not content or not content.strip():
            return ""
        try:
            from ..db.repositories import get_db_session
            from ..db.models import MemoryRecord
            record_id = str(uuid.uuid4())[:16]
            with get_db_session() as db:
                # 淘汰超出上限的旧记忆
                old_records = (
                    db.query(MemoryRecord)
                    .filter(
                        MemoryRecord.user_id == user_id,
                        MemoryRecord.persona == persona,
                        MemoryRecord.memory_type == memory_type,
                        MemoryRecord.archived_at.is_(None),
                    )
                    .order_by(MemoryRecord.created_at.asc())
                    .all()
                )
                if len(old_records) >= self.MAX_MEMORY_PER_PERSONA:
                    to_archive = old_records[: len(old_records) - self.MAX_MEMORY_PER_PERSONA + 1]
                    for r in to_archive:
                        r.archived_at = datetime.now()

                new_record = MemoryRecord(
                    id=record_id,
                    user_id=user_id,
                    persona=persona,
                    memory_type=memory_type,
                    content=content.strip(),
                    created_at=datetime.now(),
                )
                db.add(new_record)
            logger.debug("[Memory] 新增记忆 user=%s persona=%s type=%s", user_id, persona, memory_type)
            return record_id
        except Exception as exc:
            logger.warning("[Memory] add_memory 失败 user=%s: %s", user_id, exc)
            return ""

    def archive_session(
        self,
        user_id: str,
        session_id: str,
        persona: str = "general",
    ) -> str:
        """将当前会话摘要（来自 chat_sessions）写入长期记忆。

        自动从 DB 读取对话历史并用 LLM 生成摘要。
        """
        try:
            from ..db.repositories import get_db_session
            from ..db.models import ChatSession
            from ..core.llm_client import llm_client

            with get_db_session() as db:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                if not session:
                    return ""
                messages = json.loads(session.messages or "[]")

            if len(messages) < 2:
                return ""

            # 取最近 20 条构建摘要 prompt
            recent = messages[-20:]
            history_text = "\n".join(
                f"{'用户' if m.get('role') == 'user' else 'AI'}: {str(m.get('content', ''))[:200]}"
                for m in recent
            )
            prompt = (
                f"请将以下对话会话简洁归纳为 3-5 条关键记忆要点（用户学习状态、纠正的错误、达成的理解）。\n"
                f"对话内容：\n{history_text}\n"
                "返回格式：每行一条要点，以「-」开头，不超过50字。"
            )
            summary = llm_client.chat(prompt, max_tokens=300)
            if not summary.strip():
                return ""
            return self.add_memory(user_id, summary, persona=persona, memory_type="session_summary")
        except Exception as exc:
            logger.warning("[Memory] archive_session 失败 user=%s session=%s: %s", user_id, session_id, exc)
            return ""

    def clear(
        self,
        user_id: str,
        persona: Optional[str] = None,
        memory_type: Optional[str] = None,
    ) -> int:
        """清理记忆（归档标记，不物理删除）。返回清理条数。"""
        try:
            from ..db.repositories import get_db_session
            from ..db.models import MemoryRecord
            with get_db_session() as db:
                q = db.query(MemoryRecord).filter(
                    MemoryRecord.user_id == user_id,
                    MemoryRecord.archived_at.is_(None),
                )
                if persona:
                    q = q.filter(MemoryRecord.persona == persona)
                if memory_type:
                    q = q.filter(MemoryRecord.memory_type == memory_type)
                records = q.all()
                for r in records:
                    r.archived_at = datetime.now()
                return len(records)
        except Exception as exc:
            logger.warning("[Memory] clear 失败 user=%s: %s", user_id, exc)
            return 0

    def build_context_prompt(
        self,
        user_id: str,
        persona: str = "general",
        max_memories: int = 5,
    ) -> str:
        """将长期记忆格式化为系统提示词注入内容。"""
        memories = self.get_memories(user_id, persona=persona, limit=max_memories)
        if not memories:
            return ""
        lines = [f"- {m['content']}" for m in memories]
        return (
            "【该用户的历史学习记忆，请结合以下上下文提供更个性化的回答】\n"
            + "\n".join(lines)
        )


memory_manager = MemoryManager()
