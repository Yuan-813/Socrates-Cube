"""
语义切分策略：按标题/段落/逻辑块切分
"""
from typing import List
import re

def split_by_heading(text: str, max_chunk_size: int = 500) -> List[str]:
    """按标题和段落切分，保持协议流程完整性"""
    sections = re.split(r'\n#{1,3}\s', text)
    chunks = []
    
    for section in sections:
        if len(section) <= max_chunk_size:
            chunks.append(section.strip())
        else:
            paragraphs = section.split('\n\n')
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) <= max_chunk_size:
                    current_chunk += "\n\n" + para
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para
            if current_chunk:
                chunks.append(current_chunk.strip())
    
    return [c for c in chunks if len(c) > 50]
