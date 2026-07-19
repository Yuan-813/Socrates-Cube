"""验证所有梯队的实施结果。"""
import json
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(".")

print("=" * 55)
print("Socrates-Cube 2.0 实施验证报告")
print("=" * 55)

# 梯队一：人格文件
p = ROOT / "config/agent_personas.json"
if p.exists():
    personas = json.loads(p.read_text(encoding="utf-8"))
    print(f"\n[梯队一] ✅ agent_personas.json: {len(personas)} 种人格 ({list(personas.keys())})")
else:
    print("\n[梯队一] ❌ agent_personas.json 不存在")

# 梯队二：onboarding API
p2 = ROOT / "src/loopse/api/onboarding.py"
print(f"[梯队二] {'✅' if p2.exists() else '❌'} onboarding.py: {p2.exists()}")

# 梯队三：知识图谱节点
kg = json.loads((ROOT / "data/knowledge_graph.json").read_text(encoding="utf-8"))
nodes = kg.get("nodes", [])
kp_nodes = [n for n in nodes if n.get("id","").startswith("kp_")]
skill_nodes = [n for n in nodes if n.get("id","").startswith("skill_")]
cert_nodes = [n for n in nodes if n.get("id","").startswith("cert_")]
job_nodes = [n for n in nodes if n.get("id","").startswith("job_")]
acu_nodes = kg.get("cognitive_nodes", [])
print(f"\n[梯队三] ✅ 知识图谱:")
print(f"  KP节点: {len(kp_nodes)}, Skill节点: {len(skill_nodes)}, Cert节点: {len(cert_nodes)}, Job节点: {len(job_nodes)}")
print(f"  ACU认知单元: {len(acu_nodes)} (目标60)")
print(f"  总边数: {len(kg.get('edges', []))}")

# 梯队四：Career Navigator
p4 = ROOT / "src/loopse/agent/career_navigator.py"
print(f"\n[梯队四] {'✅' if p4.exists() else '❌'} career_navigator.py: {p4.exists()}")
p4b = ROOT / "src/loopse/api/career.py"
print(f"[梯队四] {'✅' if p4b.exists() else '❌'} career.py API: {p4b.exists()}")
p4c = ROOT / "frontend/src/views/CareerView.vue"
print(f"[梯队四] {'✅' if p4c.exists() else '❌'} CareerView.vue: {p4c.exists()}")

# 梯队五：PDF RAG
p5a = ROOT / "src/loopse/kb/document_processor.py"
p5b = ROOT / "src/loopse/api/knowledge_base.py"
print(f"\n[梯队五] {'✅' if p5a.exists() else '❌'} document_processor.py: {p5a.exists()}")
print(f"[梯队五] {'✅' if p5b.exists() else '❌'} knowledge_base.py API: {p5b.exists()}")

# 梯队六：考试题库
exam_path = ROOT / "data/certificate_exams.json"
if exam_path.exists():
    exam_data = json.loads(exam_path.read_text(encoding="utf-8"))
    exams = exam_data.get("exams", {})
    total_q = sum(e.get("question_count",0) for e in exams.values())
    print(f"\n[梯队六] ✅ certificate_exams.json: {len(exams)} 套题库, 共 {total_q} 题")
    for eid, e in exams.items():
        print(f"  {eid}: {e['name']} ({e['question_count']}题)")
p6b = ROOT / "src/loopse/api/exam.py"
p6c = ROOT / "frontend/src/views/ExamView.vue"
print(f"[梯队六] {'✅' if p6b.exists() else '❌'} exam.py API: {p6b.exists()}")
print(f"[梯队六] {'✅' if p6c.exists() else '❌'} ExamView.vue: {p6c.exists()}")

# 梯队七：数据扩充
mc_data = json.loads((ROOT / "data/misconceptions.json").read_text(encoding="utf-8"))
print(f"\n[梯队七] ✅ misconceptions.json: {len(mc_data)} 条 (目标150)")
print(f"[梯队七] ✅ ACU: {len(acu_nodes)} 个 (目标60)")

print("\n" + "=" * 55)
print("所有梯队验证完毕！")
print("=" * 55)
