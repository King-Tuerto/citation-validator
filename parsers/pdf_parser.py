"""
PDF Parser
----------
Extracts raw text from a PDF file using pdfplumber.
Preserves paragraph structure as best as possible.
"""

from pathlib import Path


def parse_pdf(file_path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF parsing. Run: pip install pdfplumber")

    text_parts = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())

    return "\n\n".join(text_parts)
