"""
Word Document Parser
--------------------
Extracts raw text from a .docx file using python-docx.
Preserves paragraph breaks.
"""

from pathlib import Path


def parse_docx(file_path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for Word parsing. Run: pip install python-docx")

    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
