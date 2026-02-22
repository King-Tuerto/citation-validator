"""
Manifest Checker
----------------
Reads a MANIFEST.md file (table of figures) and checks each figure
against a built-in database of attributed frameworks and models.

Outputs:
  - [manifest_name]_figure_citations.html   (open in browser)
  - Prints a ready-to-paste APA reference list to the console
"""

import sys
import io
import re
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------------------
# FRAMEWORK DATABASE
# Each entry: keyword triggers → citation metadata
# "keywords" are checked against the figure title (case-insensitive)
# ---------------------------------------------------------------------------

FRAMEWORK_DB = [

    # ── Porter ──────────────────────────────────────────────────────────────
    {
        "keywords": ["five forces", "porter's five forces", "five competitive forces"],
        "framework": "Porter's Five Forces Model",
        "authors": "Porter, M. E.",
        "year": "1980",
        "title": "Competitive Strategy: Techniques for Analyzing Industries and Competitors",
        "publisher": "Free Press",
        "apa": "Porter, M. E. (1980). *Competitive strategy: Techniques for analyzing industries and competitors*. Free Press.",
        "note": "Porter introduced the Five Forces framework to analyze industry competitiveness."
    },
    {
        "keywords": ["value chain", "porter's value chain", "porter value chain"],
        "framework": "Porter's Value Chain",
        "authors": "Porter, M. E.",
        "year": "1985",
        "title": "Competitive Advantage: Creating and Sustaining Superior Performance",
        "publisher": "Free Press",
        "apa": "Porter, M. E. (1985). *Competitive advantage: Creating and sustaining superior performance*. Free Press.",
        "note": "Porter's Value Chain was introduced in Competitive Advantage (1985), a follow-up to Competitive Strategy."
    },
    {
        "keywords": ["generic strategies", "porter's generic strategies", "porter generic"],
        "framework": "Porter's Generic Strategies",
        "authors": "Porter, M. E.",
        "year": "1980",
        "title": "Competitive Strategy: Techniques for Analyzing Industries and Competitors",
        "publisher": "Free Press",
        "apa": "Porter, M. E. (1980). *Competitive strategy: Techniques for analyzing industries and competitors*. Free Press.",
        "note": "Cost leadership, differentiation, and focus strategies were defined in Competitive Strategy (1980)."
    },
    {
        "keywords": ["diamond model", "porter diamond", "national competitive advantage"],
        "framework": "Porter's Diamond Model",
        "authors": "Porter, M. E.",
        "year": "1990",
        "title": "The Competitive Advantage of Nations",
        "publisher": "Free Press",
        "apa": "Porter, M. E. (1990). *The competitive advantage of nations*. Free Press.",
        "note": "Porter's Diamond Model explains national competitive advantage."
    },

    # ── David & David (Strategic Management textbook) ───────────────────────
    {
        "keywords": ["efe matrix", "efe process", "external factor evaluation"],
        "framework": "External Factor Evaluation (EFE) Matrix",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The EFE Matrix is a tool described and operationalized by David & David."
    },
    {
        "keywords": ["ife matrix", "ife process", "internal factor evaluation"],
        "framework": "Internal Factor Evaluation (IFE) Matrix",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The IFE Matrix is a tool described and operationalized by David & David."
    },
    {
        "keywords": ["space matrix", "space analysis", "strategic position and action evaluation"],
        "framework": "SPACE Matrix",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The SPACE Matrix was originally developed by Rowe, Mason, Dickel, Mann & Mockler (1994) but is widely taught through David & David's operationalization."
    },
    {
        "keywords": ["ie matrix", "internal-external matrix", "internal external matrix"],
        "framework": "Internal-External (IE) Matrix",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The IE Matrix is a portfolio tool described by David & David based on the GE-McKinsey framework."
    },
    {
        "keywords": ["grand strategy matrix", "grand strategy"],
        "framework": "Grand Strategy Matrix",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The Grand Strategy Matrix is attributed to David & David."
    },
    {
        "keywords": ["qspm", "quantitative strategic planning matrix", "qspm decision"],
        "framework": "Quantitative Strategic Planning Matrix (QSPM)",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The QSPM was developed by David (1986) and is fully operationalized in David & David."
    },
    {
        "keywords": ["competitive profile matrix", "cpm overview", "cpm example"],
        "framework": "Competitive Profile Matrix (CPM)",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The CPM format and methodology is attributed to David & David."
    },
    {
        "keywords": ["strategy formulation analytical framework", "formulation framework", "input stage", "matching stage", "decision stage"],
        "framework": "Strategy Formulation Analytical Framework (Three-Stage Model)",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The Input/Matching/Decision Stage framework is a David & David contribution."
    },

    # ── BCG ─────────────────────────────────────────────────────────────────
    {
        "keywords": ["bcg matrix", "bcg growth", "growth-share matrix", "growth share matrix", "stars", "cash cows", "question marks"],
        "framework": "BCG Growth-Share Matrix",
        "authors": "Boston Consulting Group",
        "year": "1970",
        "title": "The Product Portfolio",
        "publisher": "Boston Consulting Group",
        "apa": "Boston Consulting Group. (1970). *The product portfolio*. Boston Consulting Group.",
        "note": "The BCG Growth-Share Matrix was developed by Bruce Henderson at the Boston Consulting Group in 1970."
    },

    # ── Balanced Scorecard ──────────────────────────────────────────────────
    {
        "keywords": ["balanced scorecard"],
        "framework": "Balanced Scorecard",
        "authors": "Kaplan, R. S., & Norton, D. P.",
        "year": "1992",
        "title": "The Balanced Scorecard: Measures That Drive Performance",
        "publisher": "Harvard Business Review",
        "apa": "Kaplan, R. S., & Norton, D. P. (1992). The balanced scorecard: Measures that drive performance. *Harvard Business Review*, *70*(1), 71–79.",
        "note": "The Balanced Scorecard was introduced by Kaplan & Norton in their 1992 Harvard Business Review article."
    },

    # ── SWOT ────────────────────────────────────────────────────────────────
    {
        "keywords": ["swot matrix", "swot analysis"],
        "framework": "SWOT Matrix",
        "authors": "Learned, E. P., Christensen, C. R., Andrews, K. R., & Guth, W. D.",
        "year": "1969",
        "title": "Business Policy: Text and Cases",
        "publisher": "Irwin",
        "apa": "Learned, E. P., Christensen, C. R., Andrews, K. R., & Guth, W. D. (1969). *Business policy: Text and cases*. Irwin.",
        "note": "SWOT analysis originated at the Harvard Business School in the 1960s. The framework is commonly attributed to Learned et al. (1969)."
    },

    # ── PESTEL / PESTLE ─────────────────────────────────────────────────────
    {
        "keywords": ["pestel", "pestle", "pest analysis"],
        "framework": "PESTEL Analysis Framework",
        "authors": "Johnson, G., Whittington, R., Scholes, K., Angwin, D., & Regnér, P.",
        "year": "2017",
        "title": "Exploring Strategy: Text and Cases (11th ed.)",
        "publisher": "Pearson",
        "apa": "Johnson, G., Whittington, R., Scholes, K., Angwin, D., & Regnér, P. (2017). *Exploring strategy: Text and cases* (11th ed.). Pearson.",
        "note": "PESTEL (originally PEST) evolved from work by Francis Aguilar (1967). The expanded PESTEL acronym is widely attributed to Johnson et al."
    },

    # ── VRIO ────────────────────────────────────────────────────────────────
    {
        "keywords": ["vrio", "vrio framework", "vrio analysis", "vrio decision tree"],
        "framework": "VRIO Framework",
        "authors": "Barney, J. B.",
        "year": "1991",
        "title": "Firm Resources and Sustained Competitive Advantage",
        "publisher": "Journal of Management",
        "apa": "Barney, J. B. (1991). Firm resources and sustained competitive advantage. *Journal of Management*, *17*(1), 99–120.",
        "note": "The VRIO framework (Valuable, Rare, Inimitable, Organized) was developed by Jay Barney."
    },

    # ── Resource-Based View ─────────────────────────────────────────────────
    {
        "keywords": ["resource-based view", "rbv", "rbv versus", "resource based view"],
        "framework": "Resource-Based View (RBV)",
        "authors": "Barney, J. B.",
        "year": "1991",
        "title": "Firm Resources and Sustained Competitive Advantage",
        "publisher": "Journal of Management",
        "apa": "Barney, J. B. (1991). Firm resources and sustained competitive advantage. *Journal of Management*, *17*(1), 99–120.",
        "note": "The Resource-Based View was formalized by Barney (1991), building on Penrose (1959)."
    },

    # ── Ansoff Matrix ───────────────────────────────────────────────────────
    {
        "keywords": ["ansoff", "ansoff matrix", "product-market matrix", "intensive growth"],
        "framework": "Ansoff Matrix / Intensive Growth Strategies",
        "authors": "Ansoff, H. I.",
        "year": "1957",
        "title": "Strategies for Diversification",
        "publisher": "Harvard Business Review",
        "apa": "Ansoff, H. I. (1957). Strategies for diversification. *Harvard Business Review*, *35*(5), 113–124.",
        "note": "The Ansoff Matrix (product-market growth matrix) was introduced by Igor Ansoff in 1957."
    },

    # ── Triple Bottom Line ──────────────────────────────────────────────────
    {
        "keywords": ["triple bottom line", "people planet profit", "3bl"],
        "framework": "Triple Bottom Line Framework",
        "authors": "Elkington, J.",
        "year": "1997",
        "title": "Cannibals with Forks: The Triple Bottom Line of 21st Century Business",
        "publisher": "Capstone",
        "apa": "Elkington, J. (1997). *Cannibals with forks: The triple bottom line of 21st century business*. Capstone.",
        "note": "The Triple Bottom Line (people, planet, profit) concept was coined by John Elkington in 1997."
    },

    # ── Rumelt's Criteria ───────────────────────────────────────────────────
    {
        "keywords": ["rumelt", "rumelt's criteria", "rumelt's four criteria", "rumelt evaluation"],
        "framework": "Rumelt's Four Criteria for Strategy Evaluation",
        "authors": "Rumelt, R. P.",
        "year": "1980",
        "title": "The Evaluation of Business Strategy",
        "publisher": "In W. F. Glueck (Ed.), Business Policy and Strategic Management (3rd ed., pp. 359–367). McGraw-Hill.",
        "apa": "Rumelt, R. P. (1980). The evaluation of business strategy. In W. F. Glueck (Ed.), *Business policy and strategic management* (3rd ed., pp. 359–367). McGraw-Hill.",
        "note": "Rumelt's four evaluation criteria (consistency, consonance, feasibility, advantage) are from his 1980 chapter."
    },

    # ── Integration-Responsiveness Framework ────────────────────────────────
    {
        "keywords": ["integration-responsiveness", "integration responsiveness", "transnational", "global integration"],
        "framework": "Integration-Responsiveness Framework",
        "authors": "Prahalad, C. K., & Doz, Y. L.",
        "year": "1987",
        "title": "The Multinational Mission: Balancing Local Demands and Global Vision",
        "publisher": "Free Press",
        "apa": "Prahalad, C. K., & Doz, Y. L. (1987). *The multinational mission: Balancing local demands and global vision*. Free Press.",
        "note": "The Integration-Responsiveness (IR) framework was developed by Prahalad & Doz (1987)."
    },

    # ── EPS/EBIT ────────────────────────────────────────────────────────────
    {
        "keywords": ["eps/ebit", "eps ebit", "ebit analysis"],
        "framework": "EPS/EBIT Analysis",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "EPS/EBIT analysis as a capital structure decision tool is operationalized by David & David."
    },

    # ── Perceptual Map ──────────────────────────────────────────────────────
    {
        "keywords": ["perceptual map", "perceptual mapping", "positioning map"],
        "framework": "Perceptual Map",
        "authors": "Kotler, P., & Keller, K. L.",
        "year": "2016",
        "title": "Marketing Management (15th ed.)",
        "publisher": "Pearson",
        "apa": "Kotler, P., & Keller, K. L. (2016). *Marketing management* (15th ed.). Pearson.",
        "note": "Perceptual mapping is a widely used marketing tool associated with positioning theory; commonly cited through Kotler & Keller."
    },

    # ── Force Field Analysis ─────────────────────────────────────────────────
    {
        "keywords": ["force field", "force field analysis", "lewin", "driving forces", "restraining forces"],
        "framework": "Force Field Analysis",
        "authors": "Lewin, K.",
        "year": "1951",
        "title": "Field Theory in Social Science",
        "publisher": "Harper & Row",
        "apa": "Lewin, K. (1951). *Field theory in social science*. Harper & Row.",
        "note": "Force Field Analysis was developed by Kurt Lewin as part of his change management theory."
    },

    # ── Comprehensive Strategic Management Model ─────────────────────────────
    {
        "keywords": ["comprehensive strategic management model", "strategic management model"],
        "framework": "Comprehensive Strategic Management Model",
        "authors": "David, F. R., & David, F. R.",
        "year": "2017",
        "title": "Strategic Management: A Competitive Advantage Approach, Concepts and Cases (16th ed.)",
        "publisher": "Pearson",
        "apa": "David, F. R., & David, F. R. (2017). *Strategic management: A competitive advantage approach, concepts and cases* (16th ed.). Pearson.",
        "note": "The three-stage Comprehensive Strategic Management Model is the organizing framework of David & David's textbook."
    },
]


# ---------------------------------------------------------------------------
# Keywords that suggest a figure is an ORIGINAL diagram (no citation needed)
# ---------------------------------------------------------------------------
ORIGINAL_KEYWORDS = [
    "process", "flowchart", "cascade", "hierarchy", "overview",
    "comparison", "worked example", "construction example",
    "application example", "decision flow", "implementation",
    "monitoring", "integration", "pro forma", "budget hierarchy",
    "financial ratio", "dividend", "restructuring", "reengineering",
    "organic growth", "market entry modes", "objectives cascade",
    "annual objectives", "corrective actions", "evaluation characteristics",
    "contingency planning", "evaluation difficulty",
]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_manifest(manifest_path: Path):
    """
    Parse the MANIFEST.md table rows into a list of figure dicts.
    Returns: [{"fig": "2.2", "title": "...", "filename": "...", "alt": "..."}, ...]
    """
    figures = []
    current_topic = ""

    with open(manifest_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Topic heading
            if line.startswith("## "):
                current_topic = line.lstrip("# ").strip()
                continue

            # Table row (skip header and separator rows)
            if not line.startswith("|"):
                continue
            if "Figure" in line and "Title" in line:
                continue
            if line.startswith("|---") or line.startswith("| ---"):
                continue

            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]  # remove empty strings from split

            if len(parts) >= 3:
                fig_num = parts[0]
                title   = parts[1]
                filename = parts[2] if len(parts) > 2 else ""
                alt      = parts[3] if len(parts) > 3 else ""

                figures.append({
                    "fig":      fig_num,
                    "title":    title,
                    "filename": filename,
                    "alt":      alt,
                    "topic":    current_topic,
                })

    return figures


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

def check_figure(figure: dict) -> dict:
    """
    Check a single figure against the framework database.
    Returns a result dict with citation info (or a 'no citation needed' result).
    """
    title_lower = figure["title"].lower()
    alt_lower   = figure["alt"].lower()
    search_text = title_lower + " " + alt_lower

    # Check against framework DB
    for entry in FRAMEWORK_DB:
        for kw in entry["keywords"]:
            if kw.lower() in search_text:
                return {
                    "fig":       figure["fig"],
                    "title":     figure["title"],
                    "filename":  figure["filename"],
                    "topic":     figure["topic"],
                    "status":    "CITE",
                    "framework": entry["framework"],
                    "apa":       entry["apa"],
                    "note":      entry["note"],
                }

    # No match found — flag as likely original
    return {
        "fig":      figure["fig"],
        "title":    figure["title"],
        "filename": figure["filename"],
        "topic":    figure["topic"],
        "status":   "ORIGINAL",
        "framework": "",
        "apa":       "",
        "note":      "No recognized attributed framework detected. Likely an original diagram — no citation required.",
    }


# ---------------------------------------------------------------------------
# HTML Output
# ---------------------------------------------------------------------------

def generate_html(results, output_path: Path, manifest_name: str):
    cite_count     = sum(1 for r in results if r["status"] == "CITE")
    original_count = sum(1 for r in results if r["status"] == "ORIGINAL")

    # Build unique citation list (deduplicated by APA string)
    seen_apa = {}
    for r in results:
        if r["status"] == "CITE" and r["apa"] not in seen_apa:
            seen_apa[r["apa"]] = r["framework"]

    apa_list_html = ""
    for apa, framework in seen_apa.items():
        apa_list_html += f'<li>{_md_italic(apa)}</li>\n'

    # Build figure cards
    cards_html = ""
    current_topic = None
    for r in results:
        if r["topic"] != current_topic:
            current_topic = r["topic"]
            cards_html += f'<h2 class="topic-heading">{current_topic}</h2>\n'

        status    = r["status"]
        badge_cls = "badge-cite" if status == "CITE" else "badge-original"
        badge_txt = "Citation Required" if status == "CITE" else "Original — No Citation"
        icon      = "📌" if status == "CITE" else "✅"

        cards_html += f"""
<div class="card {badge_cls}-card">
  <div class="card-header">
    <span class="fig-num">Fig {r['fig']}</span>
    <span class="fig-title">{r['title']}</span>
    <span class="badge {badge_cls}">{icon} {badge_txt}</span>
  </div>
  <div class="card-body">
    <p class="filename">📄 {r['filename']}</p>
"""
        if status == "CITE":
            cards_html += f"""
    <p class="framework-label">Framework: <strong>{r['framework']}</strong></p>
    <div class="apa-block">{_md_italic(r['apa'])}</div>
    <p class="note-text">ℹ️ {r['note']}</p>
"""
        else:
            cards_html += f"""
    <p class="note-text">✏️ {r['note']}</p>
"""
        cards_html += "  </div>\n</div>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Figure Citation Report</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 0; color: #222; }}
  .toolbar {{ background: #2c3e50; color: white; padding: 14px 28px; display: flex; align-items: center; gap: 16px; }}
  .toolbar h1 {{ margin: 0; font-size: 1.2rem; flex: 1; }}
  .btn {{ padding: 8px 18px; border: none; border-radius: 5px; font-size: 0.9rem; cursor: pointer; font-weight: bold; }}
  .btn-pdf {{ background: #e74c3c; color: white; }}
  .container {{ max-width: 960px; margin: 28px auto; padding: 0 20px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat-box {{ flex: 1; min-width: 140px; background: white; border-radius: 8px; padding: 16px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); text-align: center; }}
  .stat-box .num {{ font-size: 2rem; font-weight: bold; }}
  .stat-box .lbl {{ font-size: 0.85rem; color: #666; margin-top: 4px; }}
  .num-cite {{ color: #c0392b; }}
  .num-orig {{ color: #27ae60; }}
  .num-total {{ color: #2c3e50; }}
  .topic-heading {{ color: #2c3e50; border-bottom: 2px solid #ddd; padding-bottom: 6px; margin-top: 32px; }}
  .card {{ background: white; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); overflow: hidden; }}
  .card-header {{ display: flex; align-items: center; gap: 12px; padding: 12px 18px; border-bottom: 1px solid #eee; }}
  .fig-num {{ font-weight: bold; color: #555; min-width: 52px; font-size: 0.85rem; }}
  .fig-title {{ flex: 1; font-weight: 600; font-size: 0.98rem; }}
  .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: bold; white-space: nowrap; }}
  .badge-cite {{ background: #fde8e8; color: #922; }}
  .badge-original {{ background: #e8f8ee; color: #276; }}
  .card-body {{ padding: 14px 18px; }}
  .filename {{ font-size: 0.82rem; color: #888; margin: 0 0 10px; }}
  .framework-label {{ font-size: 0.9rem; margin: 0 0 8px; }}
  .apa-block {{ background: #f0f4ff; border-left: 4px solid #3a7bd5; padding: 10px 14px; border-radius: 4px; font-size: 0.9rem; margin-bottom: 10px; }}
  .note-text {{ font-size: 0.85rem; color: #555; margin: 6px 0 0; }}
  .apa-list-section {{ background: white; border-radius: 8px; padding: 20px 24px; margin-top: 36px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .apa-list-section h2 {{ margin-top: 0; color: #2c3e50; }}
  .apa-list-section ol {{ line-height: 2; font-size: 0.92rem; }}
  .meta {{ text-align: center; color: #888; font-size: 0.82rem; margin-bottom: 20px; }}
  @media print {{ .toolbar {{ display: none; }} }}
</style>
</head>
<body>

<div class="toolbar">
  <h1>📊 Figure Citation Report — {manifest_name}</h1>
  <button class="btn btn-pdf" onclick="window.print()">🖨️ Save as PDF</button>
</div>

<div class="container">
  <p class="meta">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} &nbsp;|&nbsp; Source: {manifest_name}</p>

  <div class="summary">
    <div class="stat-box"><div class="num num-total">{len(results)}</div><div class="lbl">Total Figures</div></div>
    <div class="stat-box"><div class="num num-cite">{cite_count}</div><div class="lbl">Need Citations</div></div>
    <div class="stat-box"><div class="num num-orig">{original_count}</div><div class="lbl">Original — No Citation</div></div>
  </div>

  {cards_html}

  <div class="apa-list-section">
    <h2>📋 APA Reference List (Citations Required)</h2>
    <p style="font-size:0.85rem;color:#666;">Copy and paste these into your reference list. Figures sharing the same source are listed only once.</p>
    <ol>
{apa_list_html}
    </ol>
  </div>

</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def _md_italic(text: str) -> str:
    """Convert *italics* markdown to <em> tags for HTML display."""
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)


# ---------------------------------------------------------------------------
# Console APA summary
# ---------------------------------------------------------------------------

def print_apa_summary(results):
    seen = {}
    for r in results:
        if r["status"] == "CITE" and r["apa"] not in seen:
            seen[r["apa"]] = r["framework"]

    print("\n" + "=" * 60)
    print("  APA REFERENCES NEEDED FOR YOUR FIGURES")
    print("=" * 60)
    for i, (apa, fw) in enumerate(seen.items(), 1):
        clean = re.sub(r"\*(.+?)\*", r"\1", apa)   # strip markdown
        print(f"\n{i}. {clean}")
    print("\n" + "=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: py manifest_checker.py <path_to_MANIFEST.md>")
        sys.exit(1)

    manifest_path = Path(sys.argv[1])
    if not manifest_path.exists():
        print(f"Error: File not found: {manifest_path}")
        sys.exit(1)

    print(f"\nReading manifest: {manifest_path.name}")
    figures = parse_manifest(manifest_path)
    print(f"Found {len(figures)} figures. Checking...")

    results = [check_figure(f) for f in figures]

    cite_count     = sum(1 for r in results if r["status"] == "CITE")
    original_count = sum(1 for r in results if r["status"] == "ORIGINAL")

    print(f"\nResults: {cite_count} need citations, {original_count} are original.")

    # Output HTML
    output_path = manifest_path.parent / (manifest_path.stem + "_figure_citations.html")
    generate_html(results, output_path, manifest_path.name)
    print(f"\nHTML report saved to:\n  {output_path}")

    # Console APA list
    print_apa_summary(results)


if __name__ == "__main__":
    main()
