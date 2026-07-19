"""Build vector database from raw knowledge sources."""
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loopse.kb.text_splitter import split_text
from src.loopse.kb.vector_store import vector_store


def load_misconceptions(raw_dir: Path):
    path = raw_dir / "misconceptions.json"
    if not path.exists():
        print(f"[WARN] misconceptions.json not found at {path}")
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_protocol_specs(cleaned_dir: Path):
    specs = []
    rfc_files = sorted(cleaned_dir.glob("rfc*.md"))
    for fpath in rfc_files:
        with fpath.open("r", encoding="utf-8") as f:
            content = f.read()
        specs.append({
            "filename": fpath.name,
            "content": content,
            "rfc": fpath.stem.split("_")[0].upper(),
        })
    return specs


def load_course_docs(cleaned_dir: Path):
    docs = []
    md_files = sorted(cleaned_dir.glob("chapter*.md"))
    for fpath in md_files:
        with fpath.open("r", encoding="utf-8") as f:
            content = f.read()
        title = content.split("\n")[0].lstrip("# ").strip() if content else fpath.stem
        docs.append({
            "filename": fpath.name,
            "content": content,
            "title": title,
        })
    return docs


def build():
    root = Path(__file__).parent.parent
    raw_dir = root / "data" / "raw"
    cleaned_dir = root / "data" / "cleaned"

    print("=== Building Knowledge Base ===")

    misconceptions = load_misconceptions(raw_dir)
    print(f"Loaded {len(misconceptions)} misconceptions")

    protocol_specs = load_protocol_specs(cleaned_dir)
    print(f"Loaded {len(protocol_specs)} protocol specs")

    course_docs = load_course_docs(cleaned_dir)
    print(f"Loaded {len(course_docs)} course documents")

    vector_store.reset("misconceptions")
    if misconceptions:
        documents = []
        metadatas = []
        ids = []
        for mc in misconceptions:
            text = f"""知识点: {mc['knowledge_point']}
常见错误: {mc['misconception']}
错误类型: {mc['error_type']}
正确答案: {mc['correct_answer']}
章节: {mc['chapter']}"""
            documents.append(text)
            metadatas.append({
                "knowledge_point": mc["knowledge_point"],
                "error_type": mc["error_type"],
                "chapter": mc["chapter"],
                "source": mc.get("id", f"mc_{len(ids)}"),
            })
            ids.append(mc.get("id", f"mc_{len(ids)}"))
        vector_store.add_documents("misconceptions", documents, metadatas, ids)
        print(f"Added {len(documents)} misconceptions to vector store")

    vector_store.reset("protocol_specs")
    if protocol_specs:
        documents = []
        metadatas = []
        ids = []
        for spec in protocol_specs:
            chunks = split_text(spec["content"])
            for idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "rfc": spec["rfc"],
                    "source": spec["filename"],
                    "chunk_index": idx,
                })
                ids.append(f"{spec['rfc'].lower()}_{idx}_{uuid.uuid4().hex[:8]}")
        vector_store.add_documents("protocol_specs", documents, metadatas, ids)
        print(f"Added {len(documents)} protocol spec chunks to vector store")

    vector_store.reset("course_docs")
    if course_docs:
        documents = []
        metadatas = []
        ids = []
        for doc in course_docs:
            chunks = split_text(doc["content"])
            for idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "title": doc["title"],
                    "source": doc["filename"],
                    "chunk_index": idx,
                })
                ids.append(f"course_{doc['filename'].replace('.md', '')}_{idx}_{uuid.uuid4().hex[:8]}")
        vector_store.add_documents("course_docs", documents, metadatas, ids)
        print(f"Added {len(documents)} course doc chunks to vector store")

    course_docs_count = vector_store.count("course_docs")
    protocol_specs_count = vector_store.count("protocol_specs")
    misconceptions_count = vector_store.count("misconceptions")

    print("\n=== Knowledge Base Statistics ===")
    print(f"course_docs: {course_docs_count}")
    print(f"protocol_specs: {protocol_specs_count}")
    print(f"misconceptions: {misconceptions_count}")
    print("\nKnowledge base built successfully!")


if __name__ == "__main__":
    import sys
    build()