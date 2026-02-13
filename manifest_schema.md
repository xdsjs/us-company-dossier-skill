# Manifest Schema Documentation

## Overview
The `manifest.json` file serves as the central metadata registry for a company dossier. It contains information about the company, run details, configuration snapshot, and a complete inventory of all SEC filings and their online viewing links.

## Top-Level Structure
```json
{
  "company": {...},
  "run_info": {...},
  "config_snapshot": {...},
  "filings": [...]
}
```

## Field Definitions

### company
Contains basic company identification information.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | 股票代码（例如："AAPL"、"TSLA"） |
| company_name | string | No | 公司完整法定名称 |
| cik | string | No | SEC 中央索引键（10 位数字，补零） |
| exchange | string | No | 证券交易所（例如："NASDAQ"、"NYSE"） |
| cusip | string | No | CUSIP 标识符 |

### run_info
Metadata about the current dossier build run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| run_id | string | Yes | 本次运行的唯一标识符（推荐使用 UUID） |
| started_at | string | Yes | 运行开始时的 ISO 8601 时间戳 |
| ended_at | string | Yes | 运行结束时的 ISO 8601 时间戳 |
| status | string | Yes | 运行状态："success"、"partial_success"、"failed" |
| version | string | Yes | 生成此清单的技能版本 |

### config_snapshot
Complete snapshot of configuration used for this run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| years | integer | Yes | 请求的历史数据年数 |
| forms | array | Yes | 要获取的 SEC 表单类型列表 |
| max_filings_per_form | integer | Yes | 每种表单类型的最大文件数 |
| sec_user_agent | string | Yes | 用于 SEC 请求的 User-Agent |
| sec_rps_limit | integer | Yes | SEC 每秒请求数限制 |

### filings[]
Array of filing records with metadata and SEC viewing links.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | 此文件的稳定唯一标识符 |
| form | string | Yes | SEC 表单类型（例如："10-K"、"10-Q"、"8-K"、"DEF 14A"、"4"） |
| period | string | No | 报告期（例如：年度报告为 "2023-12-31"，季度报告为 "2023-09-30"） |
| filed_at | string | Yes | 向 SEC 提交文件时的 ISO 8601 时间戳 |
| accession_number | string | Yes | SEC 登记号（例如："0000320193-23-000106"） |
| primary_document | string | Yes | 主文档文件名 |
| url | string | Yes | SEC EDGAR 上文件的直接链接 |
| viewer_url | string | Yes | SEC 在线查看器链接，便于阅读 |
| description | string | No | 来自 SEC 的文件描述 |

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
    "max_filings_per_form": 50,
    "sec_user_agent": "OpenClawResearchBot/1.0 (research@openclaw.ai)",
    "sec_rps_limit": 5
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
      "viewer_url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=320193&accession_number=0000320193-23-000106&xbrl_type=v",
      "description": "10-K - Annual report"
    }
  ]
}
```