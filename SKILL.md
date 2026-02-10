---
name: us-company-dossier
description: Build comprehensive dossiers for US public companies with SEC filings, IR materials, and structured data. Supports fast links-only mode and full download mode.
---

# US Company Dossier Skill

**English** | [中文](SKILL.zh-CN.md)

This skill transforms OpenClaw into a "US Company Research Assistant" that automatically builds comprehensive company dossiers for US publicly traded companies.

## Overview

Given a US stock ticker (or company name), this skill:
- Automatically fetches SEC EDGAR filings metadata (10-K, 10-Q, 8-K, DEF 14A, Form 4)
- **Default Mode**: Provides SEC online viewing links without downloading files (fast, efficient)
- **Full Mode**: Downloads complete files for offline analysis (when specifically needed)
- Scrapes Investor Relations materials (press releases, presentations)
- Creates a structured, auditable, incrementally updatable dossier
- Generates normalized text and chunk indexes for RAG retrieval (full mode only)

## Core Features

### Download Modes
- **`links_only` (Default)**: Fast metadata-only mode
  - Generates SEC online viewer links for all filings
  - No file downloads - zero bandwidth and storage overhead
  - Ideal for research, analysis, and AI-assisted workflows
  - Sufficient for 95% of use cases
- **`full`**: Complete file download mode
  - Downloads all documents for offline access
  - Enables custom document processing and archival
  - Required for specialized use cases (see Usage Scenarios below)

### Data Sources
- **SEC EDGAR** (mandatory): Uses official SEC public data APIs
  - Submissions API for filing metadata
  - Direct document links or downloads based on mode
  - XBRL company facts for structured financial data
- **Investor Relations** (optional): HTTP scraping of press releases and presentations
  - Domain allowlist enforced for security
  - Browser fallback available for difficult IR sites

### Output Structure

**Links-Only Mode** (default - lightweight):
```
dossiers/{TICKER}/
├── manifest.json          # Metadata with SEC URLs and viewer links
└── logs/                  # Execution logs
```

**Full Download Mode** (when explicitly needed):
```
dossiers/{TICKER}/
├── manifest.json          # Complete audit trail
├── raw/
│   ├── sec/
│   │   ├── financial_reports/    # 10-K, 10-Q
│   │   ├── material_events/      # 8-K
│   │   ├── proxy_statements/     # DEF 14A
│   │   └── insider_transactions/ # Form 4
│   └── ir/                        # Investor relations materials
├── normalized/                    # Cleaned, structured content
├── index/                         # RAG-ready chunks
│   └── documents.jsonl
└── logs/                          # Execution logs
```

### Compliance & Safety
- **SEC Fair Access**: Strict rate limiting (≤10 requests/second)
- **Proper User-Agent**: Configurable contact information required
- **Incremental Updates**: Avoids redundant downloads
- **Domain Allowlist**: IR scraping limited to approved domains only

## Installation

### Quick Install (Recommended)

Install as a system command for easy access from anywhere:

```bash
# Navigate to the skill directory
cd /path/to/us-company-dossier-skill

# Install in development mode (editable)
pip install -e .

# Verify installation
us-dossier --help
```

### Uninstall

```bash
pip uninstall us-company-dossier
```

### Alternative: Direct Usage (No Install)

If you prefer not to install, you can still use the CLI directly:

```bash
python /path/to/us-company-dossier-skill/cli.py build --ticker AAPL
```

## Usage

### Usage Scenarios

#### When to Use `links_only` Mode (Default - Recommended)
- **Financial analysis and research**: Read filings via SEC online viewer
- **AI/LLM workflows**: Agents can access documents via provided URLs
- **Quick company overview**: Fast metadata retrieval without download delays
- **Storage-constrained environments**: No local file storage needed
- **Compliance checks**: Verify filing existence and dates
- **Most analytical use cases**: ~95% of scenarios don't require local files

#### When to Use `full` Mode (Special Requirements Only)
- **Offline access**: No internet connection available during analysis
- **Custom document processing**: Need raw HTML/XBRL parsing
- **Regulatory archival**: Legal requirement to maintain local copies
- **ML model training**: Direct file access for specialized models
- **Document immutability**: Prevent remote changes to source documents

### From OpenClaw

After installation, use the simple command format:

```python
# Default: links only mode (fast, efficient)
exec("us-dossier build TSLA --years 3")

# Full download mode (only when specifically needed)
exec("us-dossier build TSLA --years 3 --download-mode full")

# With custom workspace
exec("us-dossier build AAPL --workspace /path/to/workspace")
```

### Command Line Interface

After installation, use `us-dossier` from any directory:

```bash
# Basic usage (links only - default)
us-dossier build AAPL

# Full download mode
us-dossier build AAPL --download-mode full

# Full options with links only
us-dossier build TSLA \
  --years 5 \
  --forms 10-K 10-Q 8-K "DEF 14A" 4 \
  --include-ir \
  --max-filings-per-form 20 \
  --download-mode links_only

# Update existing dossier (incremental, respects download mode)
us-dossier update TSLA
us-dossier update TSLA --download-mode full

# Check status
us-dossier status TSLA

# List artifacts with filters
us-dossier list TSLA --form "10-K"
us-dossier list AAPL --since 2024-01-01

# Custom workspace location
us-dossier build MSFT --workspace ~/my-research
```

## Configuration

Key configuration options (set via environment variables or config file):

- `SEC_USER_AGENT`: Required contact info (e.g., "ResearchBot/1.0 (email@example.com)")
- `SEC_RPS_LIMIT`: Request rate limit (default: 3, max: 10)  
- `DOSSIER_ROOT`: Base directory for dossiers (default: ./dossiers)
- `DOMAIN_ALLOWLIST`: Comma-separated IR domains to allow
- `IR_BASE_URL_MAP`: JSON mapping of tickers to IR homepage URLs

## Quality Metrics

Each run outputs comprehensive quality metrics:
- **Completeness**: Coverage of recent required filings
- **Freshness**: Days since last update, latest filing date
- **Traceability**: 100% artifact manifest coverage with full provenance

## Dependencies

- Python 3.8+
- Core: requests, beautifulsoup4, lxml, html2text, tenacity, pydantic, markdownify, pdfminer.six
- Optional: playwright (for browser fallback mode)

Dependencies are automatically installed with `pip install -e .`

For browser fallback support (optional):
```bash
pip install playwright
playwright install chromium
```

## Examples

See `demo.py` for complete usage examples.