"""将扩展后的 150 条误解同步入 vector_store 的 misconceptions 集合。"""
import sys, io, json, hashlib
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.loopse.kb.vector_store import vector_store

mc_path = ROOT / "data" / "misconceptions.json"
items = json.loads(mc_path.read_text(encoding="utf-8"))

docs, ids, metas = [], [], []
for item in items:
    doc_id = item.get("id") or hashlib.sha1(str(len(ids)).encode()).hexdigest()[:20]
    ids.append(doc_id)
    docs.append("\n".join([
        f"知识点：{item.get('knowledge_point','')}",
        f"常见误区：{item.get('misconception','')}",
        f"错误类型：{item.get('error_type','')}",
        f"正确理解：{item.get('correct_answer','')}",
    ]))
    metas.append({
        "knowledge_point": item.get("knowledge_point",""),
        "error_type": item.get("error_type",""),
        "chapter": item.get("chapter",""),
    })

# 先清空旧数据，再全量入库
vector_store.reset("misconceptions")
vector_store.add_documents("misconceptions", docs, metas, ids)
print(f"误解库入库完成：{vector_store.count('misconceptions')} 条")
print(f"course_docs: {vector_store.count('course_docs')}")
print(f"protocol_specs: {vector_store.count('protocol_specs')}")
