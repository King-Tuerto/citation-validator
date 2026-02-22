"""
HTML Output Generator
---------------------
Produces a self-contained, styled HTML report with:
  - Summary statistics at the top
  - One card per citation showing confidence badge, URLs, claims checked
  - Color coding: GREEN = HIGH, YELLOW = MEDIUM, RED = LOW
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict


CONFIDENCE_COLORS = {
    "HIGH":   ("#d4edda", "#155724", "#28a745"),   # bg, text, badge
    "MEDIUM": ("#fff3cd", "#856404", "#ffc107"),
    "LOW":    ("#f8d7da", "#721c24", "#dc3545"),
}

CONFIDENCE_ICONS = {
    "HIGH":   "✅",
    "MEDIUM": "🟨",
    "LOW":    "❌",
}

TYPE_LABELS = {
    "article":    "Journal Article",
    "book":       "Book",
    "report":     "Corporate Report",
    "government": "Government Document",
    "web":        "Web Source",
    "unknown":    "Unknown",
}

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f6fa;
    color: #333;
    padding: 24px;
    line-height: 1.6;
}
h1 { font-size: 1.8rem; margin-bottom: 4px; }
.meta { color: #666; font-size: 0.9rem; margin-bottom: 24px; }
.summary {
    display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap;
}
.stat {
    background: white; border-radius: 8px; padding: 16px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); text-align: center; min-width: 120px;
}
.stat .number { font-size: 2rem; font-weight: 700; }
.stat .label  { font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: .05em; }
.stat.high   .number { color: #28a745; }
.stat.medium .number { color: #e6a817; }
.stat.low    .number { color: #dc3545; }
.card {
    background: white; border-radius: 10px; margin-bottom: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden;
}
.card-header {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 16px 20px; border-bottom: 1px solid #eee;
}
.badge {
    font-size: 0.75rem; font-weight: 700; padding: 3px 10px;
    border-radius: 20px; white-space: nowrap; margin-top: 2px;
    text-transform: uppercase; letter-spacing: .05em;
}
.type-pill {
    font-size: 0.7rem; color: #888; background: #f0f0f0;
    padding: 2px 8px; border-radius: 10px; white-space: nowrap; margin-top: 4px;
}
.card-key   { font-weight: 700; font-size: 1rem; }
.card-title { font-size: 0.88rem; color: #555; margin-top: 2px; }
.card-body  { padding: 16px 20px; }
.section-label {
    font-size: 0.72rem; font-weight: 700; color: #888;
    text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px;
}
.raw-citation {
    font-size: 0.85rem; color: #444; margin-bottom: 14px;
    padding: 10px 14px; background: #f8f9fa; border-radius: 6px;
    border-left: 3px solid #ccc;
}
.claims { margin-bottom: 14px; }
.claim {
    font-size: 0.85rem; color: #444; padding: 8px 14px;
    background: #f0f7ff; border-radius: 6px; margin-bottom: 6px;
    border-left: 3px solid #4a90d9;
}
.urls { list-style: none; }
.url-item {
    display: flex; align-items: flex-start; gap: 8px;
    padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 0.85rem;
}
.url-item:last-child { border-bottom: none; }
.url-score {
    font-size: 0.7rem; background: #eee; color: #555;
    padding: 1px 6px; border-radius: 10px; white-space: nowrap; margin-top: 2px;
}
.url-type-badge {
    font-size: 0.65rem; padding: 1px 6px; border-radius: 10px;
    white-space: nowrap; margin-top: 2px;
}
.url-type-source       { background: #d4edda; color: #155724; }
.url-type-claim        { background: #cce5ff; color: #004085; }
.url-type-source-claim { background: #d1ecf1; color: #0c5460; }
.url-link a { color: #1a73e8; text-decoration: none; word-break: break-all; }
.url-link a:hover { text-decoration: underline; }
.url-snippet { color: #666; font-size: 0.8rem; margin-top: 2px; }
.notes {
    font-size: 0.82rem; color: #555; padding: 8px 14px;
    border-radius: 6px; margin-top: 12px;
}
.query-row {
    font-size: 0.75rem; color: #999; margin-top: 12px;
    font-family: monospace;
}
footer { margin-top: 32px; text-align: center; color: #aaa; font-size: 0.8rem; }

/* ---- Export buttons ---- */
.toolbar {
    display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;
    align-items: center;
}
.btn {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 10px 20px; border-radius: 8px; border: none;
    font-size: 0.92rem; font-weight: 600; cursor: pointer;
    text-decoration: none; transition: opacity 0.15s;
}
.btn:hover { opacity: 0.85; }
.btn-pdf  { background: #dc3545; color: white; }
.btn-word { background: #1a73e8; color: white; }
.btn-icon { font-size: 1.1rem; }

/* ---- Rating criteria info box ---- */
.criteria-box {
    background: #eaf4fb; border: 1px solid #b8d9ee; border-radius: 10px;
    margin-bottom: 24px; overflow: hidden;
}
.criteria-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 18px; cursor: pointer; user-select: none;
    background: #d0eaf8;
}
.criteria-header:hover { background: #bde0f5; }
.criteria-title { font-weight: 700; font-size: 0.95rem; color: #1a5276; }
.criteria-toggle { font-size: 0.8rem; color: #1a5276; font-weight: 600; }
.criteria-body { padding: 16px 20px; display: none; }
.criteria-body.open { display: block; }
.criteria-grid { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }
.criteria-card {
    flex: 1; min-width: 200px; border-radius: 8px; padding: 12px 16px;
}
.criteria-card.high   { background: #d4edda; border-left: 4px solid #28a745; }
.criteria-card.medium { background: #fff3cd; border-left: 4px solid #ffc107; }
.criteria-card.low    { background: #f8d7da; border-left: 4px solid #dc3545; }
.criteria-card h4 { font-size: 0.88rem; margin-bottom: 6px; }
.criteria-card p  { font-size: 0.82rem; color: #444; line-height: 1.5; }
.criteria-sources { font-size: 0.82rem; color: #444; }
.criteria-sources b { color: #1a5276; }

/* Hide toolbar when printing so it doesn't appear in the PDF */
@media print {
    .toolbar { display: none !important; }
    body { background: white; padding: 12px; }
    .card { box-shadow: none; border: 1px solid #ddd; break-inside: avoid; }
}
"""


def _badge_html(confidence: str) -> str:
    _, text_color, bg_color = CONFIDENCE_COLORS[confidence]
    icon = CONFIDENCE_ICONS[confidence]
    return (
        f'<span class="badge" style="background:{bg_color};color:white;">'
        f'{icon} {confidence}</span>'
    )


def _card_html(citation: Dict, index: int) -> str:
    confidence = citation.get("confidence", "LOW")
    bg, _, _ = CONFIDENCE_COLORS[confidence]
    key = citation.get("key", "Unknown")
    title = citation.get("title", "")
    authors = citation.get("authors", "")
    year = citation.get("year", "")
    raw = citation.get("raw", "")
    claims = citation.get("claims", [])
    urls = citation.get("urls", [])
    notes = citation.get("notes", "")
    ctype = citation.get("type", "unknown")
    source_query = citation.get("source_query", "")
    claim_query = citation.get("claim_query", "")

    # Claims section
    claims_html = ""
    if claims:
        claim_items = "".join(
            f'<div class="claim">"{c}"</div>' for c in claims[:3]
        )
        claims_html = f"""
        <div class="claims">
            <div class="section-label">Claims Found in Document</div>
            {claim_items}
        </div>"""

    # URLs section
    urls_html = ""
    if urls:
        items = ""
        for u in urls:
            utype = u.get("type", "source").replace("+", "-")
            type_label = {
                "source": "Source",
                "claim": "Claim",
                "source-claim": "Source + Claim",
            }.get(utype, "Source")
            type_class = f"url-type-{utype}"
            items += f"""
            <li class="url-item">
                <div>
                    <div class="url-link">
                        <a href="{u['url']}" target="_blank" rel="noopener">{u['title'] or u['url']}</a>
                    </div>
                    <div class="url-snippet">{u.get('snippet','')[:160]}</div>
                </div>
                <span class="url-score">Score: {u['score']}</span>
                <span class="url-type-badge {type_class}">{type_label}</span>
            </li>"""
        urls_html = f"""
        <div class="section-label">Sources Found</div>
        <ul class="urls">{items}</ul>"""

    # Notes
    notes_html = ""
    if notes:
        note_bg = CONFIDENCE_COLORS[confidence][0]
        notes_html = f'<div class="notes" style="background:{note_bg};">{notes}</div>'

    # Query debug row
    query_html = f"""
    <div class="query-row">
        Source query: {source_query}<br>
        {f"Claim query: {claim_query}" if claim_query else ""}
    </div>"""

    return f"""
    <div class="card" id="citation-{index}">
        <div class="card-header">
            <div style="flex:1;">
                <div class="card-key">{index}. {key}</div>
                <div class="card-title">{title}</div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">
                {_badge_html(confidence)}
                <span class="type-pill">{TYPE_LABELS.get(ctype, ctype)}</span>
            </div>
        </div>
        <div class="card-body">
            <div class="section-label">Full Citation</div>
            <div class="raw-citation">{raw}</div>
            {claims_html}
            {urls_html}
            {notes_html}
            {query_html}
        </div>
    </div>"""


def generate_html(resolved: List[Dict], output_path: Path, source_doc: str = "") -> None:
    high   = sum(1 for r in resolved if r["confidence"] == "HIGH")
    medium = sum(1 for r in resolved if r["confidence"] == "MEDIUM")
    low    = sum(1 for r in resolved if r["confidence"] == "LOW")
    total  = len(resolved)
    now    = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    cards = "\n".join(_card_html(c, i + 1) for i, c in enumerate(resolved))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Citation Checker Report</title>
<style>{CSS}</style>
</head>
<body>
<h1>Citation Checker Report</h1>
<div class="meta">
    Source document: <strong>{source_doc}</strong> &nbsp;|&nbsp; Generated: {now}
</div>

<!-- Export toolbar -->
<div class="toolbar">
    <button class="btn btn-pdf" onclick="savePDF()">
        <span class="btn-icon">📄</span> Save as PDF
    </button>
    <button class="btn btn-word" onclick="saveWord()">
        <span class="btn-icon">📝</span> Save as Word
    </button>
</div>

<script>
function savePDF() {{
    window.print();
}}

function saveWord() {{
    // Grab all the citation content and build a clean Word-friendly HTML document
    var docName = "{source_doc}".replace(/[.][^/.]+$/, "");
    var cards = document.querySelectorAll('.card');
    var content = '<html><head><meta charset="UTF-8"></head><body>';
    content += '<h1>Citation Checker Report</h1>';
    content += '<p><b>Source:</b> {source_doc} &nbsp;&nbsp; <b>Generated:</b> {now}</p>';
    content += '<p><b>Total:</b> {total} citations &nbsp;|&nbsp; ';
    content += '<b style="color:green">HIGH: {high}</b> &nbsp;|&nbsp; ';
    content += '<b style="color:#e6a817">MEDIUM: {medium}</b> &nbsp;|&nbsp; ';
    content += '<b style="color:red">LOW: {low}</b></p><hr>';

    var bgColors = {{ 'HIGH': '#D4EDDA', 'MEDIUM': '#FFF3CD', 'LOW': '#F8D7DA' }};

    cards.forEach(function(card, i) {{
        var key      = card.querySelector('.card-key')   ? card.querySelector('.card-key').innerText   : '';
        var title    = card.querySelector('.card-title') ? card.querySelector('.card-title').innerText : '';
        var rawCite  = card.querySelector('.raw-citation') ? card.querySelector('.raw-citation').innerText : '';
        var badge    = card.querySelector('.badge')      ? card.querySelector('.badge').innerText      : '';
        var claims   = card.querySelectorAll('.claim');
        var urlItems = card.querySelectorAll('.url-link a');
        var notes    = card.querySelector('.notes')      ? card.querySelector('.notes').innerText      : '';

        // Work out confidence level from the badge text
        var conf = 'MEDIUM';
        if (badge.indexOf('HIGH') !== -1)   conf = 'HIGH';
        if (badge.indexOf('LOW') !== -1)    conf = 'LOW';
        var headingBg = bgColors[conf] || '#FFFFFF';

        content += '<table width="100%" cellpadding="6" cellspacing="0" style="margin-bottom:4px;border:none;"><tr><td style="background:white;border:none;"><b>' + key + '</b></td><td width="120" align="center" style="background:' + headingBg + ';border:1px solid #ccc;border-radius:4px;font-weight:bold;">' + badge + '</td></tr></table>';
        content += '<p><i>' + title + '</i></p>';
        content += '<p><b>Full Citation:</b><br>' + rawCite + '</p>';

        if (claims.length > 0) {{
            content += '<p><b>Claims in Document:</b></p><ul>';
            claims.forEach(function(c) {{ content += '<li>' + c.innerText + '</li>'; }});
            content += '</ul>';
        }}

        if (urlItems.length > 0) {{
            content += '<p><b>Sources Found:</b></p><ul>';
            urlItems.forEach(function(a) {{
                content += '<li><a href="' + a.href + '">' + a.innerText + '</a><br>' + a.href + '</li>';
            }});
            content += '</ul>';
        }}

        if (notes) {{
            content += '<p><b>Note:</b> ' + notes + '</p>';
        }}

        content += '<hr>';
    }});

    content += '</body></html>';

    // Create a downloadable .doc file (Word can open HTML-based .doc files)
    var blob = new Blob([content], {{ type: 'application/msword' }});
    var url  = URL.createObjectURL(blob);
    var a    = document.createElement('a');
    a.href     = url;
    a.download = docName + '_citations.doc';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}}
</script>

<!-- Rating criteria info box -->
<div class="criteria-box">
    <div class="criteria-header" onclick="toggleCriteria()">
        <span class="criteria-title">ℹ️ How Are Ratings Determined?</span>
        <span class="criteria-toggle" id="criteria-toggle-label">Show ▼</span>
    </div>
    <div class="criteria-body" id="criteria-body">
        <div class="criteria-grid">
            <div class="criteria-card high">
                <h4>✅ HIGH Confidence</h4>
                <p>The source was found on a <strong>highly trusted site</strong> (academic journal, publisher, DOI, Google Books, WorldCat, government site) <strong>AND</strong> the specific claim or data point from your document was independently corroborated somewhere else on the web.</p>
            </div>
            <div class="criteria-card medium">
                <h4>🟨 MEDIUM Confidence</h4>
                <p>The source appears to exist, but the specific claim could <strong>not be fully confirmed</strong> — common for paywalled journal articles where the tool can see the journal page but not the full text. OR the source was found on a moderately trusted site like Wikipedia, Forbes, or ResearchGate.</p>
            </div>
            <div class="criteria-card low">
                <h4>❌ LOW Confidence</h4>
                <p><strong>No credible source could be found</strong> for this citation anywhere on the web. This is the strongest indicator of a possible AI-hallucinated citation. Manual verification is strongly recommended before using this source.</p>
            </div>
        </div>
        <div class="criteria-sources">
            <b>Trusted sources checked (highest to lowest priority):</b>
            Academic journals &amp; DOIs (doi.org, JSTOR, PubMed) &nbsp;·&nbsp;
            Publishers (Cambridge, Oxford, Springer, Wiley, Elsevier, Pearson) &nbsp;·&nbsp;
            Google Books &amp; WorldCat &nbsp;·&nbsp;
            Government databases (.gov, BLS, Census) &nbsp;·&nbsp;
            SEC EDGAR (corporate filings) &nbsp;·&nbsp;
            Harvard Business Review &nbsp;·&nbsp;
            Academic repositories (SSRN, arXiv, ResearchGate) &nbsp;·&nbsp;
            Company investor relations pages &nbsp;·&nbsp;
            Statista &nbsp;·&nbsp;
            Major news outlets (NYT, WSJ, FT, Economist)
        </div>
    </div>
</div>
<script>
function toggleCriteria() {{
    var body  = document.getElementById('criteria-body');
    var label = document.getElementById('criteria-toggle-label');
    if (body.classList.contains('open')) {{
        body.classList.remove('open');
        label.textContent = 'Show \u25bc';
    }} else {{
        body.classList.add('open');
        label.textContent = 'Hide \u25b2';
    }}
}}
</script>

<div class="summary">
    <div class="stat"><div class="number">{total}</div><div class="label">Total Citations</div></div>
    <div class="stat high"><div class="number">{high}</div><div class="label">High Confidence</div></div>
    <div class="stat medium"><div class="number">{medium}</div><div class="label">Medium Confidence</div></div>
    <div class="stat low"><div class="number">{low}</div><div class="label">Low Confidence</div></div>
</div>

{cards}

<footer>Generated by Citation Checker &nbsp;|&nbsp; Powered by Serper.dev</footer>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
