"""验证所有Agent模块可正常import"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    "src.loopse.api.profile",
    "src.loopse.api.logs",
    "src.loopse.api.resources",
    "src.loopse.api.path",
]

for mod in modules:
    try:
        __import__(mod)
        print(f"✅ {mod}")
    except Exception as e:
        print(f"❌ {mod}: {e}")

print("\n=== Import验证完成 ===")
