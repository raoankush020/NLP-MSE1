from typing import List, Dict, Any
import re

class TextChunker:
    """Chunks text into overlapping semantic segments preserving page numbers and metadata."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = max(100, chunk_size)
        self.chunk_overlap = max(0, min(chunk_overlap, self.chunk_size // 2))

    def chunk_pages(
        self,
        pages_data: List[Dict[str, Any]],
        document_id: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        all_chunks = []
        global_chunk_idx = 0

        for page_item in pages_data:
            page_num = page_item.get("page_number", 1)
            raw_text = page_item.get("text", "")
            
            # Split page text into chunks
            page_chunks = self._split_text(raw_text)
            for chunk_str in page_chunks:
                clean_chunk = chunk_str.strip()
                if not clean_chunk:
                    continue
                all_chunks.append({
                    "chunk_index": global_chunk_idx,
                    "page_number": page_num,
                    "document_id": document_id,
                    "filename": filename,
                    "content": clean_chunk,
                })
                global_chunk_idx += 1

        return all_chunks

    def _split_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        # Use natural paragraph and sentence delimiters
        paragraphs = re.split(r'(\n{2,}|\.\s+)', text)
        units = []
        for p in paragraphs:
            if p.strip():
                units.append(p)

        chunks = []
        current_chunk = []
        current_length = 0

        for unit in units:
            unit_len = len(unit)
            if current_length + unit_len > self.chunk_size and current_chunk:
                chunk_text = "".join(current_chunk).strip()
                chunks.append(chunk_text)
                
                # Apply overlap by keeping tail elements
                overlap_accum = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    if overlap_len + len(item) <= self.chunk_overlap:
                        overlap_accum.insert(0, item)
                        overlap_len += len(item)
                    else:
                        break
                current_chunk = overlap_accum
                current_length = overlap_len

            current_chunk.append(unit)
            current_length += unit_len

        if current_chunk:
            final_text = "".join(current_chunk).strip()
            if final_text:
                chunks.append(final_text)

        # Fallback if any single chunk exceeds chunk_size heavily
        refined_chunks = []
        for ch in chunks:
            if len(ch) > self.chunk_size * 1.5:
                # hard wrap
                start = 0
                step = self.chunk_size - self.chunk_overlap
                while start < len(ch):
                    refined_chunks.append(ch[start:start + self.chunk_size].strip())
                    start += step
            else:
                refined_chunks.append(ch)

        return [c for c in refined_chunks if c]
