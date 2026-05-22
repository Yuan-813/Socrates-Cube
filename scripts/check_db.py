import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.loopse.kb.vector_store import vector_store
from src.loopse.kb.knowledge_graph import knowledge_graph

print(f"course_docs: {vector_store.get_collection_count('course_docs')}")
print(f"misconceptions: {vector_store.get_collection_count('misconceptions')}")
print(f"protocol_specs: {vector_store.get_collection_count('protocol_specs')}")
print(f"knowledge_graph nodes: {len(knowledge_graph.nodes)}")
