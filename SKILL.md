---
name: us-company-dossier
description: Build comprehensive metadata dossiers for US public companies with SEC filings links and structured data.
---

# US Company Dossier Skill

**English** | [中文](SKILL.zh-CN.md)

This skill transforms OpenClaw into a "US Company Research Assistant" that automatically builds comprehensive metadata dossiers for US publicly traded companies.

## Overview

Given a US stock ticker (or company name), this skill:
- Automatically fetches SEC EDGAR filings metadata (10-K, 10-Q, 8-K, DEF 14A, Form 4)
- Provides SEC online viewing links for all filings (fast, efficient)
- Creates a structured, auditable manifest.json file
- No file downloads - zero bandwidth and storage overhead

## Core Features

### Data Sources
- **SEC EDGAR**: Uses official SEC public data APIs
  - Submissions API for filing metadata
  - Direct document links and SEC viewer URLs
  - XBRL company facts for structured financial data

### Output Structure

```
dossiers/{TICKER}/
├── manifest.json          # Complete filing metadata with SEC viewer links
└── logs/                  # Execution logs
```

### Compliance & Safety
- **SEC Fair Access**: Strict rate limiting (≤10 requests/second)
- **Proper User-Agent**: Configurable contact information required

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

### From OpenClaw

After installation, use the simple command format:

```python
# Build a company dossier
exec("us-dossier build TSLA --years 3")

# With custom workspace
exec("us-dossier build AAPL --workspace /path/to/workspace")
```

### Command Line Interface

After installation, use `us-dossier` from any directory:

```bash
# Basic usage
us-dossier build AAPL

# With all options
us-dossier build TSLA \
  --years 5 \
  --forms 10-K 10-Q 8-K "DEF 14A" 4 \
  --max-filings-per-form 20

# Update existing dossier (incremental)
us-dossier update TSLA

# Check status
us-dossier status TSLA

# List filings with filters
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

## Quality Metrics

Each run outputs comprehensive quality metrics:
- **Completeness**: Coverage of recent required filings
- **Freshness**: Days since last update, latest filing date
- **Traceability**: 100% filing manifest coverage with full metadata

## Dependencies

- Python 3.8+
- Core: requests, pydantic

Dependencies are automatically installed with `pip install -e .`

## Examples

See `demo.py` for complete usage examples.