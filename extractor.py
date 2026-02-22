"""
Citation Extractor
------------------
Two-pass extraction from document text:

Pass 1 — Reference list
    Finds the References / Bibliography / Works Cited section and parses
    each entry into structured metadata (author, year, title, source, type).

Pass 2 — Inline citations
    Scans the body text for (Author, Year) style in-text citations, extracts
    the surrounding sentence as the "claim", and links it back to the
    reference list entry.

Each citation is returned as a dict:
{
    "key":        "Porter (1985)",          # short display key
    "authors":    "Porter, M. E.",
    "year":       "1985",
    "title":      "Competitive Advantage",
    "source":     "Free Press",             # journal, publisher, or org
    "type":       "book",                   # book | article | report | web | unknown
    "raw":        "Porter, M. E. (1985)...",# full reference list entry
    "claims":     [                         # sentences in the doc that cite this
        "...cost advantage exists when an organization delivers comparable value..."
    ]
}
"""

import re
from typing import List, Dict


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

REFERENCE_SECTION_HEADERS = re.compile(
    r"^(references|bibliography|works cited|sources|citations)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _split_body_and_references(text: str):
    """Return (body_text, references_text). If no references section found,
    references_text will be an empty string."""
    match = REFERENCE_SECTION_HEADERS.search(text)
    if not match:
        return text, ""
    split_point = match.start()
    return text[:split_point], text[split_point:]


# ---------------------------------------------------------------------------
# Reference list parsing
# ---------------------------------------------------------------------------

# Matches APA-style entries that start with Author(s). (Year).
APA_ENTRY = re.compile(
    r"^([A-ZÁÉÍÓÚÑ][^\n]+?\((\d{4}[a-z]?)\)\.\s.+?)(?=\n[A-ZÁÉÍÓÚÑ]|\Z)",
    re.MULTILINE | re.DOTALL,
)

# Detects whether entry looks like a journal article (has italicised journal
# name heuristic: comma after title, then capitalised words, then volume info)
JOURNAL_PATTERN = re.compile(r"\*?([A-Z][^,*]+)\*?,\s*\d+\(?\d*\)?")

# Corporate / organisational author (no comma = not "Last, F.")
ORG_AUTHOR = re.compile(r"^[A-Z][a-zA-Z &,\.]+\.\s*\(\d{4}\)")

# Annual / corporate report signals
REPORT_SIGNALS = re.compile(
    r"annual report|10-k|10k|sustainability report|proxy statement|"
    r"financial report|earnings report",
    re.IGNORECASE,
)

GOVT_SIGNALS = re.compile(
    r"\.gov|department of|ministry of|bureau of|office of|"
    r"united states|u\.s\. government|federal register",
    re.IGNORECASE,
)

WEB_SIGNALS = re.compile(
    r"retrieved from|https?://|www\.|\.com|\.org|\.net",
    re.IGNORECASE,
)


def _classify_type(raw: str) -> str:
    if REPORT_SIGNALS.search(raw):
        return "report"
    if GOVT_SIGNALS.search(raw):
        return "government"
    if WEB_SIGNALS.search(raw):
        return "web"
    if JOURNAL_PATTERN.search(raw):
        return "article"
    return "book"


def _parse_authors_year_title(raw: str):
    """Best-effort parse of author, year, and title from an APA entry."""
    # Year
    year_match = re.search(r"\((\d{4}[a-z]?)\)", raw)
    year = year_match.group(1) if year_match else "n.d."

    # Everything before the year = authors
    if year_match:
        authors = raw[: year_match.start()].strip().rstrip(".")
    else:
        authors = ""

    # Everything after "). " up to the next ". " or end = title
    after_year = raw[year_match.end():].strip().lstrip(". ") if year_match else raw
    title_match = re.match(r"([^.]+\.)", after_year)
    title = title_match.group(1).strip(".").strip() if title_match else after_year[:120]

    # Source = what remains after the title
    source = after_year[len(title_match.group(0)):].strip() if title_match else ""
    source = source.lstrip(". ").strip()

    return authors, year, title, source


def _parse_references(ref_text: str) -> List[Dict]:
    entries = []
    # Split on lines that look like the start of a new APA entry
    # (capital letter after a blank line)
    raw_entries = re.split(r"\n(?=[A-ZÁÉÍÓÚÑ])", ref_text)

    for raw in raw_entries:
        raw = raw.strip()
        if not raw or len(raw) < 20:
            continue
        # Skip the section header itself
        if REFERENCE_SECTION_HEADERS.match(raw):
            continue

        authors, year, title, source = _parse_authors_year_title(raw)
        if not year or not title:
            continue

        # Build short key like "Porter (1985)"
        first_author = authors.split(",")[0].strip() if authors else "Unknown"
        key = f"{first_author} ({year})"

        entries.append({
            "key": key,
            "authors": authors,
            "year": year,
            "title": title,
            "source": source,
            "type": _classify_type(raw),
            "raw": raw,
            "claims": [],
        })

    return entries


# ---------------------------------------------------------------------------
# Inline citation extraction (Pass 2)
# ---------------------------------------------------------------------------

# Matches (Author, Year), (Author & Author, Year), (Author et al., Year)
INLINE_CITE = re.compile(
    r"\(([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[,\s&]+(?:et al\.|[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+))*"
    r"(?:,\s*)?(?:\d{4}[a-z]?)(?:,\s*p+\.\s*\d+)?)\)",
    re.UNICODE,
)

# Sentence splitter
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _extract_claim_sentences(body: str, author_key: str, year: str) -> List[str]:
    """Find all sentences in body that contain an inline citation matching
    this author/year and return the sentence as the 'claim'."""
    sentences = SENTENCE_END.split(body)
    claims = []
    # Build a flexible pattern for the inline citation
    last_name = author_key.split("(")[0].strip()
    pattern = re.compile(
        rf"\({re.escape(last_name)}[^)]*{re.escape(year)}[^)]*\)",
        re.IGNORECASE,
    )
    for sentence in sentences:
        if pattern.search(sentence):
            clean = sentence.strip().replace("\n", " ")
            if len(clean) > 20:
                claims.append(clean)
    return claims


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_citations(document_text: str) -> List[Dict]:
    """
    Main entry point. Returns a list of citation dicts, each with a
    'claims' list of sentences from the document body that use the citation.
    """
    body, ref_text = _split_body_and_references(document_text)

    if not ref_text:
        print("      Warning: No References section found. Attempting full-document scan.")
        ref_text = document_text
        body = document_text

    citations = _parse_references(ref_text)

    # Pass 2: attach claims from body text
    for citation in citations:
        citation["claims"] = _extract_claim_sentences(
            body, citation["key"], citation["year"]
        )

    return citations
