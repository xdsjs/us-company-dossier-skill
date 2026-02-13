# US Company Dossier Skill

[English](README.md) | [中文](README.zh-CN.md)

This skill transforms OpenClaw into a "US Stock Company Research Assistant" that automatically builds comprehensive metadata dossiers from SEC EDGAR filings.

## Overview

The `us_company_dossier` skill fetches SEC filing metadata and generates a structured manifest with online viewing links, creating a lightweight, auditable company research index.

### Key Features

- **SEC EDGAR Integration**: Automatically fetches metadata for 10-K, 10-Q, 8-K, DEF 14A, and Form 4 filings
- **Online Viewing Links**: Generates SEC document and viewer URLs without downloading files
- **Traceable Metadata**: Every filing includes accession number, filing date, and SEC links
- **Incremental Updates**: Efficiently updates existing dossiers with new filings
- **Compliance Ready**: Respects SEC rate limits and user-agent requirements
- **Zero Storage**: No file downloads - only metadata and links

## Installation

### Quick Install (Recommended)

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

## Configuration

Create a `.env` file in your workspace root or set these environment variables:

```bash
# Required: SEC User-Agent (must include contact info)
SEC_USER_AGENT="YourResearchBot/1.0 (your-email@example.com)"

# Optional: Rate limiting (default: 3 requests/second, max: 10)
SEC_RPS_LIMIT=3

# Optional: Dossier output directory (default: ./dossiers)
DOSSIER_ROOT="/path/to/dossiers"
```

## Usage

### Python API

```python
from us_company_dossier import build_dossier

# Build dossier for Tesla (TSLA)
result = build_dossier(
    ticker="TSLA",
    years=3
)

print(f"Dossier created at: {result['dossier_path']}")
print(f"Filings indexed: {result['summary']['total_filings']}")
print(f"Latest filing: {result['summary']['latest_filed_at']}")
```

### Command Line Interface

```bash
# Build dossier
us-dossier build TSLA --years 3

# Update existing dossier (incremental)
us-dossier update TSLA

# Check status
us-dossier status TSLA

# List filings
us-dossier list TSLA --form 10-K
us-dossier list AAPL --since 2024-01-01
```

### Parameters

#### `build_dossier()` / `update_dossier()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ticker` | str | Required | Stock ticker symbol (e.g., "AAPL", "TSLA") |
| `years` | int | 3 | Number of years of historical data to fetch |
| `forms` | List[str] | ["10-K", "10-Q", "8-K", "DEF 14A", "4"] | SEC form types to fetch |
| `max_filings_per_form` | int | 50 | Maximum filings per form type |
| `force_rebuild` | bool | False | Force full rebuild (ignore existing data) |
| `workspace_root` | str | None | Override workspace root directory |
| `dossier_root` | str | None | Override dossier output directory |

## Output Structure

```
dossiers/{TICKER}/
├── manifest.json          # Filing metadata with SEC viewer links
└── logs/
    └── {timestamp}.log    # Execution log
```

### Manifest Schema

The `manifest.json` file contains:

```json
{
  "company": {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "cik": "0000320193",
    "exchange": "NASDAQ"
  },
  "run_info": {
    "run_id": "uuid",
    "started_at": "2026-02-10T12:00:00Z",
    "ended_at": "2026-02-10T12:15:30Z",
    "status": "success",
    "version": "1.0.0"
  },
  "config_snapshot": {
    "years": 3,
    "forms": ["10-K", "10-Q", "8-K", "DEF 14A", "4"],
    "max_filings_per_form": 50,
    "sec_user_agent": "...",
    "sec_rps_limit": 3
  },
  "filings": [
    {
      "id": "10k-2023-09-30",
      "form": "10-K",
      "period": "2023-09-30",
      "filed_at": "2023-11-03T16:32:05Z",
      "accession_number": "0000320193-23-000106",
      "primary_document": "aapl-20230930.htm",
      "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
      "viewer_url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=320193&accession_number=0000320193-23-000106",
      "description": "10-K - Annual report"
    }
  ]
}
```

See [manifest_schema.md](manifest_schema.md) for complete schema documentation.

## Quality Metrics

Each run outputs:
- **Completeness**: Coverage of required filings (10-K, 10-Q, etc.)
- **Freshness**: Days since last filing, latest filing date
- **Traceability**: 100% metadata coverage with SEC links

## Dependencies

- Python 3.8+
- requests
- pydantic

Install with: `pip install -e .`

## Examples

See [demo.py](demo.py) for complete usage examples.

## Compliance & Legal

- **SEC Fair Access**: This skill respects SEC EDGAR's fair access policy (≤10 req/s)
- **User-Agent Required**: Must provide valid contact information in `SEC_USER_AGENT`
- **Data Usage**: All data fetched from public SEC APIs
- **No Warranties**: Data provided as-is for research purposes

## License

MIT License - See LICENSE file for details
