import os
from typing import List, Dict, Any
from pathlib import Path
import pypdf
import docx

class DocumentParser:
    """Parses text from various document formats (PDF, DOCX, TXT, MD) with page tracking."""

    @staticmethod
    def parse_file(file_path: str) -> List[Dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            return DocumentParser._parse_pdf(file_path)
        elif ext == ".docx":
            return DocumentParser._parse_docx(file_path)
        elif ext in [".txt", ".md", ".markdown"]:
            return DocumentParser._parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported: .pdf, .docx, .txt, .md")

    @staticmethod
    def _parse_pdf(file_path: str) -> List[Dict[str, Any]]:
        pages_content = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            num_pages = len(reader.pages)
            if num_pages == 0:
                raise ValueError("PDF document is empty.")
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                clean_text = text.strip()
                if clean_text:
                    pages_content.append({
                        "page_number": i + 1,
                        "text": clean_text
                    })

        if not pages_content:
            raise ValueError("No readable text found in PDF document.")
        return pages_content

    @staticmethod
    def _parse_docx(file_path: str) -> List[Dict[str, Any]]:
        doc = docx.Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            raise ValueError("DOCX document is empty or contains no readable text.")

        # Estimate pagination by paragraphs block or treat as single page document
        full_text = "\n\n".join(paragraphs)
        return [{
            "page_number": 1,
            "text": full_text
        }]

    @staticmethod
    def _parse_text(file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        if not text:
            raise ValueError("Document file is empty.")
        return [{
            "page_number": 1,
            "text": text
        }]
