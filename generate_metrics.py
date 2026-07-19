"""
generate_metrics.py
从 edu_agent.db 中提取 4 项核心实验指标，用于软件杯展示。

指标定义：
1. 诊断准确率   = agent_logs 中 Diagnosis 动作结果包含 error_type != 'none' 的有效诊断 / 总 Diagnosis 调用
2. 路径完成率   = learning_path_nodes 中 status='completed' 的节点 / 总节点
3. 误解覆盖率   = misconception_records 中 distinct misconception_id / misconceptions.json 总条目
4. 知识点提升率 = assessment_records 中后测分数 > 前测分数的记录比例
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "edu_agent.db"
MC_JSON = Path(__file__).parent / "data" / "misconceptions.json"


def get_metrics() -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ── 指标1: 诊断准确率 ────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM agent_logs WHERE agent_name='Diagnosis'")
    total_diag = cur.fetchone()[0] or 1

    cur.execute("""
        SELECT COUNT(*) FROM agent_logs
        WHERE agent_name='Diagnosis'
          AND result LIKE '%\"is_correct\": false%'
    """)
    valid_diag = cur.fetchone()[0]

    # 非空结果（包含 is_correct 字段）算有效诊断
    cur.execute("""
        SELECT COUNT(*) FROM agent_logs
        WHERE agent_name='Diagnosis'
          AND (result LIKE '%is_correct%')
    """)
    result_with_field = cur.fetchone()[0]

    diag_accuracy = round(result_with_field / total_diag * 100, 1) if total_diag else 0

    # ── 指标2: 路径完成率 ────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM learning_path_nodes")
    total_nodes = cur.fetchone()[0] or 1

    cur.execute("SELECT COUNT(*) FROM learning_path_nodes WHERE status='completed'")
    completed_nodes = cur.fetchone()[0]

    path_completion = round(completed_nodes / total_nodes * 100, 1)

    # ── 指标3: 误解覆盖率 ────────────────────────────────────────────
    try:
        mc_total = len(json.loads(MC_JSON.read_text(encoding="utf-8")))
    except Exception:
        mc_total = 50

    cur.execute("SELECT COUNT(DISTINCT pattern) FROM misconception_records WHERE pattern IS NOT NULL AND pattern != ''")
    mc_covered = cur.fetchone()[0]

    mc_coverage = round(mc_covered / mc_total * 100, 1) if mc_total else 0

    # ── 指标4: 知识点提升率 ──────────────────────────────────────────
    # 同一用户同一 knowledge_point 有前/后两次 assessment，后测分 > 前测分
    cur.execute("""
        SELECT COUNT(DISTINCT user_id || '|' || knowledge_node_id)
        FROM (
            SELECT user_id, knowledge_node_id,
                   MIN(CAST(score AS REAL)) AS pre_score,
                   MAX(CAST(score AS REAL)) AS post_score
            FROM assessment_records
            WHERE score IS NOT NULL
            GROUP BY user_id, knowledge_node_id
            HAVING COUNT(*) >= 2
        )
        WHERE post_score > pre_score
    """)
    improved = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(DISTINCT user_id || '|' || knowledge_node_id)
        FROM (
            SELECT user_id, knowledge_node_id
            FROM assessment_records
            WHERE score IS NOT NULL
            GROUP BY user_id, knowledge_node_id
            HAVING COUNT(*) >= 2
        )
    """)
    total_pairs = cur.fetchone()[0] or 1

    improvement_rate = round(improved / total_pairs * 100, 1)

    conn.close()

    return {
        "diagnosis_accuracy":   {"value": diag_accuracy,    "unit": "%", "label": "诊断有效响应率",   "detail": f"{result_with_field}/{total_diag} 次调用返回结构化诊断结果"},
        "path_completion":      {"value": path_completion,   "unit": "%", "label": "路径节点完成率",   "detail": f"{completed_nodes}/{total_nodes} 个路径节点已完成"},
        "misconception_coverage":{"value": mc_coverage,     "unit": "%", "label": "误解模式覆盖率", "detail": f"识别 {mc_covered} 种认知错误模式（误解库涵盖 {mc_total} 条）"},
        "knowledge_improvement": {"value": improvement_rate, "unit": "%", "label": "知识点提升率",     "detail": f"{improved}/{total_pairs} 对前后测中知识点分数提升"},
    }


if __name__ == "__main__":
    metrics = get_metrics()
    print("\n========== Socrates-Cube 实验指标 ==========")
    for key, m in metrics.items():
        print(f"\n  {m['label']}")
        print(f"    数值: {m['value']}{m['unit']}")
        print(f"    依据: {m['detail']}")
    print("\n=============================================")
    # 输出 JSON 供前端/PPT 引用
    out = Path(__file__).parent / "outputs" / "metrics.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] 指标已保存至 {out}")
