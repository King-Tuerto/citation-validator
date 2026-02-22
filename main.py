# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

"""
Citation Checker
----------------
Parses a PDF, Word, or Markdown document, extracts all citations and the
claims attached to them, searches the web for corroborating sources, and
outputs an HTML report and an annotated Word document.

Usage:
    python main.py <path_to_document>
    python main.py "my_paper.pdf"
    python main.py "my_paper.docx"
    python main.py "my_paper.md"
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from parsers.pdf_parser import parse_pdf
from parsers.docx_parser import parse_docx
from parsers.md_parser import parse_md
from extractor import extract_citations
from resolver import resolve_citations
from output.html_output import generate_html
from output.docx_output import generate_docx


load_dotenv()


SUPPORTED_EXTENSIONS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".md": parse_md,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_document>")
        print("Supported formats: .pdf, .docx, .md")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"Error: File not found — {input_path}")
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"Error: Unsupported file type '{ext}'")
        print(f"Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}")
        sys.exit(1)

    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("Error: SERPER_API_KEY not set in .env file")
        print("Copy .env.example to .env and add your key from serper.dev")
        sys.exit(1)

    print(f"\nCitation Checker")
    print(f"{'=' * 50}")
    print(f"Document: {input_path.name}")

    # Step 1: Parse the document into raw text
    print(f"\n[1/4] Parsing document...")
    parser = SUPPORTED_EXTENSIONS[ext]
    document_text = parser(input_path)
    print(f"      Done — {len(document_text):,} characters extracted")

    # Step 2: Extract citations and their associated claims
    print(f"\n[2/4] Extracting citations and claims...")
    citations = extract_citations(document_text)
    print(f"      Found {len(citations)} citations")
    for i, c in enumerate(citations, 1):
        print(f"      {i:>3}. {c['key']}")

    # Step 3: Resolve each citation against live web sources
    print(f"\n[3/4] Resolving citations via web search...")
    print(f"      (This may take a moment — one search per citation)")
    resolved = resolve_citations(citations, api_key)

    verified = sum(1 for r in resolved if r["confidence"] == "HIGH")
    medium = sum(1 for r in resolved if r["confidence"] == "MEDIUM")
    low = sum(1 for r in resolved if r["confidence"] == "LOW")
    print(f"      HIGH confidence:   {verified}")
    print(f"      MEDIUM confidence: {medium}")
    print(f"      LOW confidence:    {low}  ← review these carefully")

    # Step 4: Generate outputs
    print(f"\n[4/4] Generating output files...")

    stem = input_path.stem
    output_dir = input_path.parent

    html_path = output_dir / f"{stem}_citations.html"
    generate_html(resolved, html_path, source_doc=input_path.name)
    print(f"      HTML report: {html_path}")

    docx_path = output_dir / f"{stem}_with_urls.docx"
    generate_docx(resolved, docx_path, source_doc=input_path.name)
    print(f"      Word copy:   {docx_path}")

    print(f"\n{'=' * 50}")
    print(f"Done. {len(resolved)} citations processed.")
    if low > 0:
        print(f"WARNING: {low} citation(s) could not be verified — possible hallucination.")
    print()


if __name__ == "__main__":
    main()
