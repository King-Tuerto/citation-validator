"""
Markdown Parser
---------------
Extracts raw text from a Markdown file.
Strips markdown syntax to give the extractor clean prose.
"""

import re
from pathlib import Path


def parse_md(file_path: Path) -> str:
    raw = file_path.read_text(encoding="utf-8")

    # Remove image tags
    raw = re.sub(r"!\[.*?\]\(.*?\)", "", raw)
    # Remove inline links but keep the link text
    raw = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", raw)
    # Remove HTML tags
    raw = re.sub(r"<[^>]+>", "", raw)
    # Remove bold/italic markers
    raw = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", raw)
    raw = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", raw)
    # Remove heading markers but keep text
    raw = re.sub(r"^#{1,6}\s+", "", raw, flags=re.MULTILINE)
    # Remove horizontal rules
    raw = re.sub(r"^[-*_]{3,}\s*$", "", raw, flags=re.MULTILINE)
    # Remove table formatting characters
    raw = re.sub(r"\|", " ", raw)
    # Collapse multiple blank lines
    raw = re.sub(r"\n{3,}", "\n\n", raw)

    return raw.strip()
