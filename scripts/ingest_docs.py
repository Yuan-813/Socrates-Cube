"""
文档入库脚本 - 将 data/cleaned/ 下的 Markdown 课程文本
切分后批量写入 ChromaDB 的 course_docs 集合
"""
import os
import sys
import re
import json
import hashlib
import argparse
import logging

# 确保项目 src 在 Python 路径内
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s  %(message)s')
log = logging.getLogger(__name__)

CLEANED_DIR = os.path.join(ROOT, 'data', 'cleaned')
MISCONCEPTIONS_FILE = os.path.join(ROOT, 'data', 'raw', 'misconceptions.json')

CHUNK_SIZE = 400   # 每块目标字符数
OVERLAP    = 80    # 块间重叠字符数


# ------------------------------------------------------------------ #
# 文本切分
# ------------------------------------------------------------------ #
def _split_by_heading(text: str) -> list[str]:
    """按二级标题先粗切，再按 CHUNK_SIZE 细分"""
    sections = re.split(r'\n(?=##\s)', text)
    chunks: list[str] = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) <= CHUNK_SIZE:
            chunks.append(sec)
        else:
            # 滑动窗口细切
            start = 0
            while start < len(sec):
                end = min(start + CHUNK_SIZE, len(sec))
                chunks.append(sec[start:end])
                start += CHUNK_SIZE - OVERLAP
    return [c for c in chunks if len(c.strip()) > 20]


def _doc_id(source: str, idx: int) -> str:
    raw = f"{source}_{idx}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


# ------------------------------------------------------------------ #
# 入库：课程文档
# ------------------------------------------------------------------ #
def ingest_course_docs(collection, dry_run: bool = False) -> int:
    total = 0
    md_files = [f for f in os.listdir(CLEANED_DIR) if f.endswith('.md')]
    if not md_files:
        log.warning('data/cleaned/ 下没有找到 .md 文件，跳过课程文档入库')
        return 0

    for fname in sorted(md_files):
        fpath = os.path.join(CLEANED_DIR, fname)
        with open(fpath, encoding='utf-8') as f:
            raw = f.read()

        chapter = fname.replace('.md', '')
        chunks = _split_by_heading(raw)
        log.info(f'  {fname}: {len(chunks)} 个文本块')

        for i, chunk in enumerate(chunks):
            doc_id = _doc_id(fname, i)
            meta = {'source': fname, 'chapter': chapter, 'chunk_index': i}
            if not dry_run:
                collection.upsert(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[meta]
                )
            total += 1

    return total


# ------------------------------------------------------------------ #
# 入库：误解条目
# ------------------------------------------------------------------ #
def ingest_misconceptions(collection, dry_run: bool = False) -> int:
    if not os.path.exists(MISCONCEPTIONS_FILE):
        log.warning('misconceptions.json 不存在，跳过误解库入库')
        return 0

    with open(MISCONCEPTIONS_FILE, encoding='utf-8') as f:
        items = json.load(f)

    log.info(f'误解库条目数: {len(items)}')
    for item in items:
        doc_id = item.get('id', _doc_id('misc', hash(str(item))))
        text = (
            f"误解：{item.get('misconception', '')}\n"
            f"正确理解：{item.get('correct_concept', item.get('correct_answer', ''))}"
        )
        meta = {
            'knowledge_point': item.get('knowledge_point', ''),
            'error_type': item.get('error_type', ''),
            'chapter': item.get('chapter', ''),
        }
        if not dry_run:
            collection.upsert(ids=[doc_id], documents=[text], metadatas=[meta])

    return len(items)


# ------------------------------------------------------------------ #
# 主入口
# ------------------------------------------------------------------ #
def main():
    parser = argparse.ArgumentParser(description='将课程文档和误解库写入 ChromaDB')
    parser.add_argument('--dry-run', action='store_true', help='只切分不写库，用于调试')
    parser.add_argument('--reset', action='store_true', help='清空集合后重新入库')
    args = parser.parse_args()

    if args.dry_run:
        log.info('=== DRY RUN 模式，不实际写入 ===')
        course_chunks = 0
        for fname in sorted(os.listdir(CLEANED_DIR)):
            if not fname.endswith('.md'):
                continue
            with open(os.path.join(CLEANED_DIR, fname), encoding='utf-8') as f:
                raw = f.read()
            chunks = _split_by_heading(raw)
            log.info(f'  {fname}: {len(chunks)} 个文本块，示例:\n    {chunks[0][:80]}...')
            course_chunks += len(chunks)
        log.info(f'合计 {course_chunks} 个课程文本块（未写库）')
        return

    # 正式写入
    from loopse.kb.vector_store import vector_store

    course_col = vector_store.course_docs
    misc_col   = vector_store.misconceptions

    if args.reset:
        log.info('--reset: 清空现有集合...')
        for col in (course_col, misc_col):
            existing = col.get()
            if existing['ids']:
                col.delete(ids=existing['ids'])
        log.info('清空完成')

    log.info('--- 开始入库：课程文档 ---')
    n_docs = ingest_course_docs(course_col)

    log.info('--- 开始入库：误解库 ---')
    n_misc = ingest_misconceptions(misc_col)

    log.info(f'=== 入库完成：课程文档 {n_docs} 块 | 误解条目 {n_misc} 条 ===')


if __name__ == '__main__':
    main()
