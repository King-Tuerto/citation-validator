# Citation Checker

Validates citations in academic documents by searching the web for each
cited source and the specific claim attached to it. Detects hallucinated
or incorrect citations that AI writing tools sometimes produce.

## What It Does

1. **Parses** a PDF, Word (.docx), or Markdown (.md) document
2. **Extracts** every citation from the References section plus the
   sentence(s) in the document body that use each citation (the "claim")
3. **Searches** the web (via Serper.dev) for:
   - The source itself (does this book/article/report actually exist?)
   - The specific claim (does this data point appear anywhere credible?)
4. **Scores** each citation HIGH / MEDIUM / LOW confidence
5. **Outputs** two files:
   - `[filename]_citations.html` — styled, clickable HTML report
   - `[filename]_with_urls.docx` — Word document with URLs appended

## Confidence Levels

| Level | Meaning |
|-------|---------|
| HIGH | Source found at authoritative domain AND claim corroborated |
| MEDIUM | Source found but claim not directly confirmed (may be paywalled) |
| LOW | No credible source found — possible hallucination, manual review required |

## Setup

### 1. Get a free Serper.dev API key
- Go to [serper.dev](https://serper.dev) and sign up
- No credit card required — 2,500 free queries included
- Copy your API key from the dashboard

### 2. Configure your key
```bash
cp .env.example .env
# Edit .env and paste your SERPER_API_KEY
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py "path/to/document.pdf"
python main.py "path/to/document.docx"
python main.py "path/to/document.md"
```

Output files are saved in the same folder as the input document.

## Example Output (console)

```
Citation Checker
==================================================
Document: Topic-1-Foundations-of-Strategic-Management.md

[1/4] Parsing document...
      Done — 42,817 characters extracted

[2/4] Extracting citations and claims...
      Found 9 citations
        1. Candido (2015)
        2. David (2017)
        3. Gittell (2005)
        ...

[3/4] Resolving citations via web search...
      [1/9] Candido (2015)... HIGH
      [2/9] David (2017)... MEDIUM
      [3/9] Gittell (2005)... HIGH
      ...
      HIGH confidence:   6
      MEDIUM confidence: 2
      LOW confidence:    1  ← review these carefully

[4/4] Generating output files...
      HTML report: Topic-1-Foundations-of-Strategic-Management_citations.html
      Word copy:   Topic-1-Foundations-of-Strategic-Management_with_urls.docx

==================================================
Done. 9 citations processed.
WARNING: 1 citation(s) could not be verified — possible hallucination.
```

## Supported Citation Formats

- APA (primary target)
- Most formats with a References / Bibliography / Works Cited section

## Supported Document Types

| Format | Parser |
|--------|--------|
| PDF | pdfplumber |
| Word (.docx) | python-docx |
| Markdown (.md) | built-in |

## Project Structure

```
Citation-Checker/
├── main.py              # CLI entry point
├── extractor.py         # Citation + claim extraction
├── resolver.py          # Serper.dev web search + confidence scoring
├── parsers/
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   └── md_parser.py
├── output/
│   ├── html_output.py
│   └── docx_output.py
├── tests/
│   └── sample_docs/     # Place test documents here
├── requirements.txt
├── .env.example
└── README.md
```

## Limitations

- Cannot verify the exact text quoted from a source (full text often paywalled)
- Very recent sources (post-2023) may have limited web presence
- Highly obscure publications may return LOW confidence even if real
- Page numbers and specific quotes cannot be validated, only the source's existence
