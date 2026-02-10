# Manifest Schema Documentation

## Overview
The `manifest.json` file serves as the central metadata registry for a company dossier. It contains information about the company, run details, configuration snapshot, and a complete inventory of all artifacts collected during the dossier build process.

## Top-Level Structure
```json
{
  "company": {...},
  "run_info": {...},
  "config_snapshot": {...},
  "artifacts": [...]
}
```

## Field Definitions

### company
Contains basic company identification information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | Stock ticker symbol (e.g., "AAPL", "TSLA") |
| company_name | string | No | Full legal company name |
| cik | string | No | SEC Central Index Key (10-digit zero-padded) |
| exchange | string | No | Stock exchange (e.g., "NASDAQ", "NYSE") |
| cusip | string | No | CUSIP identifier |

### run_info
Metadata about the current dossier build run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| run_id | string | Yes | Unique identifier for this run (UUID recommended) |
| started_at | string | Yes | ISO 8601 timestamp when run started |
| ended_at | string | Yes | ISO 8601 timestamp when run ended |
| status | string | Yes | Run status: "success", "partial_success", "failed" |
| version | string | Yes | Skill version that generated this manifest |

### config_snapshot
Complete snapshot of configuration used for this run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| years | integer | Yes | Number of years of historical data requested |
| forms | array | Yes | List of SEC form types to fetch |
| include_ir | boolean | Yes | Whether IR materials were included |
| max_filings_per_form | integer | Yes | Maximum filings per form type |
| force_rebuild | boolean | Yes | Whether forced rebuild was enabled |
| normalize_level | string | Yes | Normalization level: "none", "light", "deep" |
| fetch_mode | string | Yes | Fetch mode: "http" or "browser_fallback" |
| sec_user_agent | string | Yes | User-Agent used for SEC requests |
| sec_rps_limit | integer | Yes | SEC requests per second limit |
| domain_allowlist | array | Yes | Allowed domains for IR scraping |

### artifacts[]
Array of artifact records, one per downloaded file.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Stable unique identifier for this artifact |
| source | string | Yes | Source type: "sec" or "ir" |
| type | string | Yes | Artifact type: "filing", "exhibit", "xbrl", "press", "presentation", "other" |
| form | string | No | SEC form type (e.g., "10-K", "10-Q", "8-K", "DEF 14A", "4") |
| period | string | No | Reporting period (e.g., "2023-12-31" for annual, "2023-09-30" for quarterly) |
| filed_at | string | No | ISO 8601 timestamp when filing was submitted to SEC |
| url | string | Yes | Original source URL |
| local_path | string | Yes | Relative path within dossier directory |
| content_type | string | Yes | MIME content type (e.g., "text/html", "application/pdf") |
| size_bytes | integer | Yes | File size in bytes |
| sha256 | string | Yes | SHA-256 hash of file contents |
| downloaded_at | string | Yes | ISO 8601 timestamp when file was downloaded |
| parse_status | string | Yes | Parsing status: "pending", "success", "failed" |
| parse_error | string | No | Error message if parsing failed |
| versioning | object | Yes | Versioning information |

#### versioning object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| is_new | boolean | Yes | Whether this is a newly downloaded artifact |
| replaced_artifact_id | string | No | ID of previous artifact this replaces (if any) |

## Example Manifest
```json
{
  "company": {
    "ticker": "AAPL",
    "company_name": "Apple Inc.",
    "cik": "0000320193",
    "exchange": "NASDAQ"
  },
  "run_info": {
    "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "started_at": "2026-02-10T12:00:00Z",
    "ended_at": "2026-02-10T12:15:30Z",
    "status": "success",
    "version": "1.0.0"
  },
  "config_snapshot": {
    "years": 3,
    "forms": ["10-K", "10-Q", "8-K", "DEF 14A", "4"],
    "include_ir": true,
    "max_filings_per_form": 50,
    "force_rebuild": false,
    "normalize_level": "light",
    "fetch_mode": "http",
    "sec_user_agent": "OpenClawResearchBot/1.0 (research@openclaw.ai)",
    "sec_rps_limit": 5,
    "domain_allowlist": ["investor.apple.com"]
  },
  "artifacts": [
    {
      "id": "sec_filing_0000320193_000032019323000106_10k",
      "source": "sec",
      "type": "filing",
      "form": "10-K",
      "period": "2023-09-30",
      "filed_at": "2023-11-03T16:32:05Z",
      "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
      "local_path": "raw/sec/filings/20231103_10-k.htm",
      "content_type": "text/html",
      "size_bytes": 1254321,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "downloaded_at": "2026-02-10T12:05:23Z",
      "parse_status": "success",
      "versioning": {
        "is_new": true
      }
    }
  ]
}
```