"""
Chroma向量库封装
"""
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import os

class VectorStore:
    def __init__(self, persist_dir: str = "./data/vector_db"):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
    
    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.ef
        )
    
    def add_documents(
        self, 
        collection_name: str, 
        documents: List[str], 
        metadatas: List[Dict],
        ids: List[str]
    ):
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(
        self, 
        collection_name: str, 
        query: str, 
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        collection = self.get_or_create_collection(collection_name)
        if collection.count() == 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            where=where
        )
        return results

vector_store = VectorStore()
