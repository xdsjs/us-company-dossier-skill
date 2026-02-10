# US Company Dossier Skill

[English](README.md) | [中文](README.zh-CN.md)

This skill transforms OpenClaw into a "US Stock Company Research Assistant" that automatically builds comprehensive company dossiers from SEC EDGAR filings and Investor Relations materials.

## Overview

The `us_company_dossier` skill fetches, archives, and normalizes public company information to create locally auditable, incrementally updatable, and searchable company research packages.

### Key Features

- **SEC EDGAR Integration**: Automatically fetches 10-K, 10-Q, 8-K, DEF 14A, and Form 4 filings
- **Flexible Download Modes**: 
  - `links_only` (default): Generates SEC document links without downloading files - ideal for quick research and online viewing
  - `full`: Downloads complete files for offline analysis and archival
- **IR Material Collection**: Gathers press releases, presentations, and earnings materials
- **Traceable Archiving**: Every document includes source URL, timestamp, hash, and metadata
- **Incremental Updates**: Avoids re-downloading unchanged content
- **Searchable Index**: Creates normalized text chunks for RAG retrieval (full mode only)
- **Compliance Ready**: Respects SEC rate limits and user-agent requirements

## Installation

The skill is automatically available when placed in the OpenClaw skills directory.

## Configuration

Create a `.env` file in your workspace root or set these environment variables:

```bash
# Required: SEC User-Agent (must include contact info)
SEC_USER_AGENT="YourResearchBot/1.0 (your-email@example.com)"

# Optional: Rate limiting (default: 2 requests/second, max: 10)
SEC_RPS_LIMIT=2

# Optional: Workspace root (default: current directory)
WORKSPACE_ROOT="/path/to/your/workspace"

# Optional: Dossier output directory (default: {WORKSPACE_ROOT}/dossiers)
DOSSIER_ROOT="/path/to/dossiers"

# Optional: Domain allowlist for IR sites
DOMAIN_ALLOWLIST="investor.example.com,ir.example.com"

# Optional: Ticker to IR URL mapping
IR_BASE_URL_MAP='{"AAPL": "https://investor.apple.com", "MSFT": "https://www.microsoft.com/investor"}'
```

## Usage

### Basic Usage

```python
from us_company_dossier import build_dossier

# Build dossier for Tesla (TSLA) - links only mode (default)
result = build_dossier(
    ticker="TSLA",
    years=3,
    include_ir=True,
    normalize_level="light",
    download_mode="links_only"  # Default: generates SEC links without downloading
)

print(f"Dossier created at: {result['dossier_path']}")
print(f"Filings indexed: {result['summary']['downloaded_count']}")
print(f"Latest filing: {result['summary']['latest_filed_at']}")

# Full download mode (for offline access or custom processing)
result_full = build_dossier(
    ticker="TSLA",
    years=3,
    download_mode="full"  # Downloads all files
)
```

### Command Line Interface

```bash
# Build dossier (links only mode by default)
python -m us_company_dossier build --ticker TSLA --years 3 --include-ir

# Build dossier with full download mode
python -m us_company_dossier build --ticker TSLA --years 3 --download-mode full

# Update existing dossier (incremental)
python -m us_company_dossier update --ticker TSLA

# Check status
python -m us_company_dossier status --ticker TSLA

# List artifacts
python -m us_company_dossier list --ticker TSLA --form 10-K
```

### Parameters

#### `build_dossier()` / `update_dossier()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ticker` | str | **required** | Stock ticker symbol (e.g., "TSLA") |
| `years` | int | 3 | Number of years of historical data to fetch |
| `forms` | list | `["10-K", "10-Q", "8-K", "DEF 14A", "4"]` | SEC form types to include |
| `include_ir` | bool | True | Include Investor Relations materials |
| `max_filings_per_form` | int | 50 | Maximum filings per form type |
| `force_rebuild` | bool | False | Force re-download all content |
| `normalize_level` | str | "light" | Normalization level: "none", "light", or "deep" |
| `fetch_mode` | str | "http" | Fetch mode: "http" or "browser_fallback" |
| `download_mode` | str | "links_only" | Download mode: "links_only" or "full" |

### Download Mode Usage Scenarios

#### `links_only` Mode (Default - Recommended for Most Use Cases)

**Use this mode when:**
- Performing financial analysis, due diligence, or research tasks
- You need quick access to filing metadata and SEC online viewing links
- Working with AI agents or LLMs that can read documents via URLs
- Building a research index or catalog
- Bandwidth or storage is limited
- You want faster execution (no download wait time)

**Benefits:**
- **Instant results**: No file download delays
- **Zero storage**: Only metadata is stored locally
- **Always up-to-date**: SEC online viewer shows the latest version
- **Lower bandwidth**: No large file transfers
- **Sufficient for 95% of analytical use cases**: Most AI/LLM-based analysis can access documents via the provided SEC URLs

#### `full` Mode (For Special Requirements)

**Only use this mode when:**
- You need **offline access** (no internet connection available)
- Performing **custom document processing** that requires raw HTML/XBRL parsing
- **Regulatory archival** requirements mandate local file storage
- Building **specialized ML models** that need direct file access
- Need to ensure **document immutability** (prevent remote changes)

**Trade-offs:**
- Slower execution (file download time)
- Higher bandwidth usage
- Requires significant storage space
- Risk of SSL errors or network interruptions
- Files may become outdated over time

#### Return Value

Returns a dictionary with:
- `dossier_path`: Path to the created dossier directory
- `summary`: Summary statistics including download counts and latest dates
- `errors`: List of any errors encountered
- `quality_metrics`: Completeness, freshness, and traceability metrics

## Output Structure

### Links-Only Mode (Default)

In `links_only` mode, the dossier contains only metadata and URLs:

```
dossiers/{TICKER}/
├── manifest.json          # Metadata with SEC URLs and viewer links
└── logs/
    └── run_*.log          # Execution logs
```

The `manifest.json` contains all filing metadata with:
- `url`: Direct link to SEC document
- `metadata.viewer_url`: SEC online viewer URL
- `metadata.raw_url`: Raw document URL
- `parse_status`: Set to "links_only"

### Full Download Mode

In `full` mode, complete files are downloaded:

```
dossiers/{TICKER}/
├── manifest.json          # Complete metadata and audit trail
├── raw/
│   ├── sec/
│   │   ├── financial_reports/    # 10-K, 10-Q filings
│   │   ├── material_events/      # 8-K filings
│   │   ├── proxy_statements/     # DEF 14A
│   │   └── insider_transactions/ # Form 4
│   └── ir/
│       ├── press/                # Press releases
│       └── presentations/        # Investor presentations
├── normalized/                   # Cleaned, structured content
│   ├── sec/
│   └── ir/
├── index/
│   └── documents.jsonl           # Searchable chunks for RAG
└── logs/
    └── run_*.log                 # Execution logs
```

## Compliance

This skill strictly adheres to SEC EDGAR access requirements:

- **Rate Limiting**: Respects 10 requests/second maximum (default: 2 rps)
- **User-Agent**: Requires valid contact information in User-Agent header
- **Fair Access**: Implements exponential backoff for 429/503 errors
- **No Authentication**: Only accesses publicly available data

## Examples

### Example 1: Basic Company Research (Links Only)

```python
from us_company_dossier import build_dossier

# Create a comprehensive dossier for Apple with links only (default)
result = build_dossier(
    ticker="AAPL",
    years=5,
    forms=["10-K", "10-Q", "8-K"],
    download_mode="links_only",  # Default mode
    include_ir=True
)

print(f"Created dossier for {result['company_info']['company_name']}")
print(f"Indexed {len(result['artifacts'])} filings")

# Access SEC links from manifest
for artifact in result['artifacts']:
    if artifact['type'] == 'filing':
        print(f"{artifact['form']}: {artifact['metadata']['viewer_url']}")
```

### Example 2: Incremental Update

```python
from us_company_dossier import update_dossier

# Only fetch new filings since last run
result = update_dossier(ticker="MSFT")
if result['summary']['downloaded_count'] > 0:
    print(f"Updated MSFT dossier with {result['summary']['downloaded_count']} new documents")
```

### Example 3: Full Download Mode (For Offline Access)

```python
from us_company_dossier import build_dossier

# Download files for offline analysis
result = build_dossier(
    ticker="TSLA",
    years=2,
    download_mode="full",  # Download complete files
    normalize_level="light"
)

print(f"Downloaded {result['summary']['downloaded_count']} files")
print(f"Dossier size: {result['summary'].get('total_bytes', 0) / 1024 / 1024:.2f} MB")
```

### Example 4: RAG Integration (Full Mode)

```python
import json

# Load the index for retrieval (only available in full mode)
with open("dossiers/TSLA/index/documents.jsonl", "r") as f:
    chunks = [json.loads(line) for line in f]

# Find chunks about competition
competition_chunks = [
    chunk for chunk in chunks 
    if "competition" in chunk.get("text", "").lower()
]

for chunk in competition_chunks[:3]:
    print(f"Source: {chunk['source_url']}")
    print(f"Text: {chunk['text'][:200]}...")
    print("---")
```

## Quality Metrics

Each run produces quality metrics to ensure data reliability:

- **Completeness**: Verifies recent required filings are present
- **Freshness**: Reports how current the data is
- **Traceability**: Ensures every piece of data can be traced to its source

## Limitations

- Does not handle paywalled or login-required content
- PDF parsing may fail on complex layouts (no OCR by default)
- Browser fallback only enabled for IR sites when HTTP fails
- Limited to US public companies with SEC filings

## Support

For issues or feature requests, please check the OpenClaw documentation or community forums.