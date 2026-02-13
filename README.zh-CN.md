# 美国上市公司档案技能

[English](README.md) | [中文](README.zh-CN.md)

本技能将 OpenClaw 转变为"美国股票公司研究助手"，自动从 SEC EDGAR 文件构建全面的元数据档案。

## 概述

`us_company_dossier` 技能获取 SEC 文件元数据并生成包含在线查看链接的结构化清单，创建轻量级、可审计的公司研究索引。

### 核心特性

- **SEC EDGAR 集成**：自动获取 10-K、10-Q、8-K、DEF 14A 和 Form 4 文件的元数据
- **在线查看链接**：生成 SEC 文档和查看器 URL，无需下载文件
- **可追溯元数据**：每个文件包含登记号、提交日期和 SEC 链接
- **增量更新**：高效更新现有档案，添加新文件
- **合规就绪**：遵守 SEC 速率限制和 User-Agent 要求
- **零存储**：无文件下载 - 仅元数据和链接

## 安装

### 快速安装（推荐）

```bash
# 切换到技能目录
cd /path/to/us-company-dossier-skill

# 以开发模式安装（可编辑）
pip install -e .

# 验证安装
us-dossier --help
```

### 卸载

```bash
pip uninstall us-company-dossier
```

## 配置

在工作空间根目录创建 `.env` 文件或设置以下环境变量：

```bash
# 必需：SEC User-Agent（必须包含联系信息）
SEC_USER_AGENT="YourResearchBot/1.0 (your-email@example.com)"

# 可选：速率限制（默认：3 请求/秒，最大：10）
SEC_RPS_LIMIT=3

# 可选：档案输出目录（默认：./dossiers）
DOSSIER_ROOT="/path/to/dossiers"
```

## 使用方法

### Python API

```python
from us_company_dossier import build_dossier

# 为特斯拉（TSLA）构建档案
result = build_dossier(
    ticker="TSLA",
    years=3
)

print(f"档案创建于: {result['dossier_path']}")
print(f"已索引文件: {result['summary']['total_filings']}")
print(f"最新文件: {result['summary']['latest_filed_at']}")
```

### 命令行界面

```bash
# 构建档案
us-dossier build TSLA --years 3

# 更新现有档案（增量）
us-dossier update TSLA

# 检查状态
us-dossier status TSLA

# 列出文件
us-dossier list TSLA --form 10-K
us-dossier list AAPL --since 2024-01-01
```

### 参数

#### `build_dossier()` / `update_dossier()`

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `ticker` | str | 必需 | 股票代码（例如："AAPL"、"TSLA"） |
| `years` | int | 3 | 获取历史数据的年数 |
| `forms` | List[str] | ["10-K", "10-Q", "8-K", "DEF 14A", "4"] | 要获取的 SEC 表格类型 |
| `max_filings_per_form` | int | 50 | 每种表格类型的最大文件数 |
| `force_rebuild` | bool | False | 强制完全重建（忽略现有数据） |
| `workspace_root` | str | None | 覆盖工作空间根目录 |
| `dossier_root` | str | None | 覆盖档案输出目录 |

## 输出结构

```
dossiers/{TICKER}/
├── manifest.json          # 包含 SEC 查看器链接的文件元数据
└── logs/
    └── {timestamp}.log    # 执行日志
```

### 清单模式

`manifest.json` 文件包含：

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
      "description": "10-K - 年度报告"
    }
  ]
}
```

完整的模式文档参见 [manifest_schema.md](manifest_schema.md)。

## 质量指标

每次运行输出：
- **完整性**：必需文件（10-K、10-Q 等）的覆盖率
- **新鲜度**：距上次提交的天数、最新提交日期
- **可追溯性**：100% 元数据覆盖率，包含 SEC 链接

## 依赖项

- Python 3.8+
- requests
- pydantic

安装：`pip install -e .`

## 示例

完整使用示例参见 [demo.py](demo.py)。

## 合规与法律

- **SEC 公平访问**：本技能遵守 SEC EDGAR 公平访问政策（≤10 请求/秒）
- **User-Agent 必需**：必须在 `SEC_USER_AGENT` 中提供有效的联系信息
- **数据使用**：所有数据从公共 SEC API 获取
- **无担保**：数据按原样提供，仅用于研究目的

## 许可证

MIT 许可证 - 详见 LICENSE 文件
