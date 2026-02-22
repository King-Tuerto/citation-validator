"""
Citation Resolver
-----------------
For each citation:
  1. Build a targeted search query based on citation type and available claims
  2. Query the Serper.dev Google Search API
  3. Score results by source trustworthiness
  4. Return top URLs and a confidence level (HIGH / MEDIUM / LOW)

Confidence levels:
  HIGH   — Source found at a trusted domain AND claim corroborated
  MEDIUM — Source found but claim only partially corroborated, or source
            found at a less authoritative domain
  LOW    — No credible source found; possible hallucination
"""

import time
import re
import requests
from typing import List, Dict


# ---------------------------------------------------------------------------
# Trusted domain scoring
# ---------------------------------------------------------------------------

DOMAIN_SCORES = {
    # Highest trust — primary publishers and authoritative databases
    "doi.org": 10,
    "jstor.org": 10,
    "pubmed.ncbi.nlm.nih.gov": 10,
    "scholar.google.com": 9,
    "books.google.com": 9,
    "worldcat.org": 9,
    "loc.gov": 9,
    "sec.gov": 10,          # SEC EDGAR for corporate filings
    # Publisher / journal sites
    "hbr.org": 8,
    "cambridge.org": 9,
    "oxford.org": 9,
    "springer.com": 9,
    "wiley.com": 9,
    "tandfonline.com": 9,
    "sagepub.com": 9,
    "emerald.com": 8,
    "elsevier.com": 9,
    "pearson.com": 8,
    "mcgrawhill.com": 8,
    # Academic repositories
    "researchgate.net": 7,
    "academia.edu": 7,
    "ssrn.com": 8,
    "arxiv.org": 8,
    # Company investor relations
    "ir.netflix.net": 9,
    "investor.apple.com": 9,
    "investors.google.com": 9,
    # Reference / encyclopedic
    "wikipedia.org": 5,
    "britannica.com": 6,
    # News — reputable outlets
    "nytimes.com": 6,
    "wsj.com": 6,
    "ft.com": 6,
    "economist.com": 6,
    "forbes.com": 5,
    "businessinsider.com": 4,
    # Data
    "statista.com": 7,
    "bls.gov": 9,
    "census.gov": 9,
    "data.gov": 9,
}

DEFAULT_SCORE = 3   # unknown domains


def _domain_score(url: str) -> int:
    for domain, score in DOMAIN_SCORES.items():
        if domain in url:
            return score
    return DEFAULT_SCORE


# ---------------------------------------------------------------------------
# Query builders per citation type
# ---------------------------------------------------------------------------

def _build_query(citation: Dict) -> str:
    title = citation.get("title", "")
    authors = citation.get("authors", "")
    year = citation.get("year", "")
    source = citation.get("source", "")
    ctype = citation.get("type", "unknown")
    claims = citation.get("claims", [])

    # Pull the first claim's key data phrase (first 12 words) if available
    claim_phrase = ""
    if claims:
        words = claims[0].split()
        # Strip the inline citation from the claim for cleaner searching
        clean = re.sub(r"\([^)]+\d{4}[^)]*\)", "", claims[0]).strip()
        claim_words = clean.split()[:12]
        claim_phrase = " ".join(claim_words)

    if ctype == "article":
        # Search by title + journal + year — most precise for articles
        q = f'"{title}" {authors.split(",")[0]} {year}'
        if source:
            q += f' "{source.split(",")[0]}"'
        return q

    if ctype == "book":
        q = f'"{title}" {authors.split(",")[0]} {year}'
        return q

    if ctype == "report":
        # For corporate reports lean on claim data if we have it
        org = authors.split(".")[0].strip()
        if claim_phrase:
            return f'{org} {year} annual report "{claim_phrase}"'
        return f'{org} {year} annual report'

    if ctype == "government":
        org = authors.split(".")[0].strip()
        return f'{org} "{title}" {year} site:.gov OR filetype:pdf'

    if ctype == "web":
        # For web citations, title is usually descriptive enough
        return f'"{title}" {authors.split(".")[0]} {year}'

    # Fallback: title + first author + year
    first_author = authors.split(",")[0].strip() if authors else ""
    return f'"{title}" {first_author} {year}'


def _build_claim_query(citation: Dict) -> str:
    """Secondary query focused on the specific claim/data point."""
    claims = citation.get("claims", [])
    if not claims:
        return ""
    # Clean the first claim — remove the inline citation marker
    clean = re.sub(r"\([^)]+\d{4}[^)]*\)", "", claims[0]).strip()
    # Take a meaningful phrase (roughly the first 15 words)
    words = clean.split()[:15]
    return " ".join(words)


# ---------------------------------------------------------------------------
# Serper API call
# ---------------------------------------------------------------------------

SERPER_URL = "https://google.serper.dev/search"


def _search(query: str, api_key: str, num: int = 5) -> List[Dict]:
    """Call Serper and return a list of organic results."""
    if not query.strip():
        return []
    try:
        response = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": num},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("organic", [])
    except requests.RequestException as e:
        print(f"      Search error: {e}")
        return []


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def _score_results(source_results: List[Dict], claim_results: List[Dict]) -> tuple:
    """
    Returns (confidence, urls, notes) where:
      confidence — HIGH / MEDIUM / LOW
      urls       — list of {url, title, snippet, score} dicts
      notes      — human-readable explanation of the confidence level
    """
    all_results = []

    for r in source_results:
        url = r.get("link", "")
        score = _domain_score(url)
        all_results.append({
            "url": url,
            "title": r.get("title", ""),
            "snippet": r.get("snippet", ""),
            "score": score,
            "type": "source",
        })

    claim_urls = set()
    for r in claim_results:
        url = r.get("link", "")
        claim_urls.add(url)
        # If already in all_results, boost its score
        existing = next((x for x in all_results if x["url"] == url), None)
        if existing:
            existing["score"] += 2
            existing["type"] = "source+claim"
        else:
            score = _domain_score(url)
            all_results.append({
                "url": url,
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "score": score,
                "type": "claim",
            })

    # Sort by score descending
    all_results.sort(key=lambda x: x["score"], reverse=True)
    top = all_results[:5]

    if not top:
        return "LOW", [], "No results found for this citation."

    best_score = top[0]["score"]
    has_claim_corroboration = any(r["type"] in ("source+claim", "claim") for r in top[:3])

    if best_score >= 8 and has_claim_corroboration:
        confidence = "HIGH"
        notes = "Source found at authoritative domain; specific claim corroborated."
    elif best_score >= 8:
        confidence = "MEDIUM"
        notes = "Source found at authoritative domain; claim not directly corroborated (may be paywalled)."
    elif best_score >= 5:
        confidence = "MEDIUM"
        notes = "Source found at moderately trusted domain."
    elif best_score >= DEFAULT_SCORE and len(top) >= 2:
        confidence = "MEDIUM"
        notes = "Source found but only at general or low-authority domains."
    else:
        confidence = "LOW"
        notes = "Could not locate a credible source. Manual verification required."

    return confidence, top, notes


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_citations(citations: List[Dict], api_key: str) -> List[Dict]:
    """
    Resolve each citation. Adds 'confidence', 'urls', and 'notes' keys.
    Returns the enriched list.
    """
    resolved = []

    for i, citation in enumerate(citations, 1):
        key = citation["key"]
        print(f"      [{i}/{len(citations)}] {key}...", end=" ", flush=True)

        # Primary search: verify the source exists
        source_query = _build_query(citation)
        source_results = _search(source_query, api_key, num=5)

        # Secondary search: corroborate the specific claim
        claim_query = _build_claim_query(citation)
        claim_results = _search(claim_query, api_key, num=5) if claim_query else []

        confidence, urls, notes = _score_results(source_results, claim_results)
        print(confidence)

        resolved.append({
            **citation,
            "source_query": source_query,
            "claim_query": claim_query,
            "confidence": confidence,
            "urls": urls,
            "notes": notes,
        })

        # Be polite to the API — avoid rate limiting
        if i < len(citations):
            time.sleep(0.5)

    return resolved
