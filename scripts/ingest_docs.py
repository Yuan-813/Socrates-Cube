"""
将 data/cleaned/ 下的Markdown文件和 misconceptions.json 向量化，存入Chroma
"""
import os
import sys
import json
sys.path.insert(0, os.path.abspath('.'))

from src.loopse.kb.vector_store import vector_store
from src.loopse.utils.text_splitter import split_by_heading

def ingest_course_docs():
    cleaned_dir = "data/cleaned"
    if not os.path.exists(cleaned_dir):
        os.makedirs(cleaned_dir)
        
    chapter_files = [f for f in os.listdir(cleaned_dir) if f.endswith('.md')]
    if not chapter_files:
        print("⚠ 没有找到课程文档。跳过...")
        return
        
    all_chunks = []
    all_ids = []
    all_metadatas = []
    
    for filename in chapter_files:
        filepath = os.path.join(cleaned_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        chunks = split_by_heading(text)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "source": filename,
                "chapter": filename.split('_')[0],
                "chunk_index": i
            })
    
    if all_chunks:
        vector_store.add_documents("course_docs", all_chunks, all_metadatas, all_ids)
        print(f"✅ 已向量化 {len(all_chunks)} 个文本块 (course_docs)")

def ingest_misconceptions():
    raw_path = "data/raw/misconceptions.json"
    if not os.path.exists(raw_path):
        print("⚠ 未找到 misconceptions.json，跳过...")
        return
        
    with open(raw_path, "r", encoding="utf-8") as f:
        misconceptions = json.load(f)
    
    documents = [f"{m['misconception']}\n正确理解：{m['correct_answer']}" 
                 for m in misconceptions]
    ids = [m["id"] for m in misconceptions]
    metadatas = [{"error_type": m["error_type"], 
                  "knowledge_point": m["knowledge_point"],
                  "chapter": m["chapter"]} 
                 for m in misconceptions]
    
    if documents:
        vector_store.add_documents("misconceptions", documents, metadatas, ids)
        print(f"✅ 已向量化 {len(documents)} 条误解记录 (misconceptions)")

if __name__ == "__main__":
    ingest_course_docs()
    ingest_misconceptions()
