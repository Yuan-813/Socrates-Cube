import sys, os, asyncio, warnings, json, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
load_dotenv()

results = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status))
    print(f"  [{status}] {name} {detail}")

# 1. 模块导入
print("\n=== [1. 模块导入] ===")
modules = [
    "src.loopse.core.llm_client",
    "src.loopse.kb.vector_store",
    "src.loopse.kb.knowledge_graph",
    "src.loopse.agent.coordinator",
    "src.loopse.agent.retriever",
    "src.loopse.agent.diagnosis",
    "src.loopse.agent.profiler",
    "src.loopse.agent.orchestrator",
    "src.loopse.agent.resource_generator",
    "src.loopse.agent.path_planner",
    "src.loopse.db.repositories",
    "src.loopse.api.resources",
    "src.loopse.api.path",
]
for mod in modules:
    try:
        __import__(mod)
        check(mod, True)
    except Exception as e:
        check(mod, False, str(e)[:60])

# 2. ChromaDB
print("\n=== [2. ChromaDB] ===")
try:
    from src.loopse.kb.vector_store import vector_store
    cd = vector_store.get_collection_count("course_docs")
    mc = vector_store.get_collection_count("misconceptions")
    check("course_docs>=30", cd >= 30, f"actual={cd}")
    check("misconceptions>=20", mc >= 20, f"actual={mc}")
except Exception as e:
    check("ChromaDB", False, str(e)[:60])

# 3. 知识图谱
print("\n=== [3. 知识图谱] ===")
try:
    from src.loopse.kb.knowledge_graph import knowledge_graph
    nodes = list(knowledge_graph.nodes.values())
    edges = knowledge_graph.edges
    chapters = set(n.get("chapter", "") for n in nodes)
    check("nodes>=20", len(nodes) >= 20, f"actual={len(nodes)}")
    check("edges>=18", len(edges) >= 18, f"actual={len(edges)}")
    check("chapters>=5", len(chapters) >= 5, f"actual={len(chapters)}")
except Exception as e:
    check("KnowledgeGraph", False, str(e)[:80])
    traceback.print_exc()

# 4. Prompt
print("\n=== [4. Prompt文件] ===")
from pathlib import Path
prompt_dir = Path("config/prompts")
prompt_files = list(prompt_dir.rglob("*.txt"))
check("prompts>=8", len(prompt_files) >= 8, f"actual={len(prompt_files)}")
for f in sorted(prompt_files):
    print(f"    {f.relative_to('config/prompts')}")

# 5. DeepSeek API
print("\n=== [5. DeepSeek API] ===")
from src.loopse.core.llm_client import llm_client
try:
    r = llm_client.chat("1+1=? 只回答数字")
    check("sync_call", bool(r and "LLM" not in r), f"result={r[:30]}")
except Exception as e:
    check("sync_call", False, str(e)[:60])

async def test_stream():
    chunks = []
    try:
        async for t in llm_client.async_stream_chat("1+1=? 只回答数字"):
            chunks.append(t)
        check("stream_call", len(chunks) > 0, f"tokens={len(chunks)}")
    except Exception as e:
        check("stream_call", False, str(e)[:60])

asyncio.run(test_stream())

# 6. 单元测试
print("\n=== [6. 单元测试] ===")
import unittest
loader = unittest.TestLoader()
suite = loader.discover("tests/unit", pattern="test_*.py")
runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
result = runner.run(suite)
ok = result.testsRun - len(result.failures) - len(result.errors)
check("unit_tests", ok == result.testsRun and result.testsRun > 0, f"{ok}/{result.testsRun}")

# 7. Orchestrator
print("\n=== [7. Orchestrator全链路] ===")
from src.loopse.db.connection import init_db
from src.loopse.agent.orchestrator import orchestrator

async def test_chain():
    try:
        await init_db()
        events = []
        full_text = ""
        async for raw in orchestrator.process_message(
            session_id="v1", user_id="u1",
            user_message="什么是TCP三次握手"
        ):
            e = json.loads(raw)
            evt = e.get("event", "")
            events.append(evt)
            if evt == "token":
                data = e.get("data", "")
                full_text += data if isinstance(data, str) else str(data)
        has_token = "token" in events
        has_done = "done" in events
        check("orchestrator_chain", has_token and has_done,
              f"events={events[:8]}... answer={full_text[:60]}")
    except Exception as e:
        check("orchestrator_chain", False, str(e)[:80])
        traceback.print_exc()

asyncio.run(test_chain())

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, s in results if s == "PASS")
total = len(results)
print(f"  TOTAL: {passed}/{total} PASSED")
if passed == total:
    print("  ALL CHECKS PASSED!")
else:
    failed = [n for n, s in results if s == "FAIL"]
    print(f"  FAILED: {failed}")
print("=" * 60)
