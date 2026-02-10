# 美国上市公司档案技能

[English](README.md) | [中文](README.zh-CN.md)

这个技能将 OpenClaw 转变为"美国股票公司研究助手"，自动从 SEC EDGAR 文件和投资者关系材料构建全面的公司档案。

## 概述

`us_company_dossier` 技能获取、归档和标准化上市公司信息，创建本地可审计、增量更新和可搜索的公司研究包。

### 核心特性

- **SEC EDGAR 集成**：自动获取 10-K、10-Q、8-K、DEF 14A 和 Form 4 文件
- **灵活的下载模式**：
  - `links_only`（默认）：生成 SEC 文档链接而不下载文件 - 适合快速研究和在线查看
  - `full`：下载完整文件用于离线分析和存档
- **IR 材料收集**：收集新闻稿、演示文稿和财报材料
- **可追溯归档**：每个文档都包含源 URL、时间戳、哈希值和元数据
- **增量更新**：避免重复下载未更改的内容
- **可搜索索引**：创建标准化文本块用于 RAG 检索（仅全量模式）
- **合规就绪**：遵守 SEC 速率限制和 User-Agent 要求

## 安装

### 快速安装（推荐）

将项目安装为系统命令，便于在任何位置访问：

```bash
# 导航到技能目录
cd /Users/jss/clawd/skills/us_company_dossier

# 以开发模式安装（可编辑）
pip install -e .

# 验证安装
us-dossier --help
```

### 卸载

```bash
pip uninstall us-company-dossier
```

### 备选方案：直接使用（无需安装）

如果不想安装，仍可直接使用 CLI：

```bash
python /Users/jss/clawd/skills/us_company_dossier/cli.py build AAPL
```

## 配置

在工作区根目录创建 `.env` 文件或设置这些环境变量：

```bash
# 必需：SEC User-Agent（必须包含联系信息）
SEC_USER_AGENT="YourResearchBot/1.0 (your-email@example.com)"

# 可选：速率限制（默认：2 请求/秒，最大：10）
SEC_RPS_LIMIT=2

# 可选：工作区根目录（默认：当前目录）
WORKSPACE_ROOT="/path/to/your/workspace"

# 可选：档案输出目录（默认：{WORKSPACE_ROOT}/dossiers）
DOSSIER_ROOT="/path/to/dossiers"

# 可选：IR 站点域名白名单
DOMAIN_ALLOWLIST="investor.example.com,ir.example.com"

# 可选：股票代码到 IR URL 映射
IR_BASE_URL_MAP='{"AAPL": "https://investor.apple.com", "MSFT": "https://www.microsoft.com/investor"}'
```

## 使用方法

### Python API 基本用法

```python
from us_company_dossier import build_dossier

# 为 Tesla (TSLA) 构建档案 - 仅链接模式（默认）
result = build_dossier(
    ticker="TSLA",
    years=3,
    include_ir=True,
    normalize_level="light",
    download_mode="links_only"  # 默认：生成 SEC 链接而不下载
)

print(f"档案创建于：{result['dossier_path']}")
print(f"已索引文件：{result['summary']['downloaded_count']}")
print(f"最新文件：{result['summary']['latest_filed_at']}")

# 全量下载模式（用于离线访问或自定义处理）
result_full = build_dossier(
    ticker="TSLA",
    years=3,
    download_mode="full"  # 下载所有文件
)
```

### 命令行界面

安装后，可在任何目录使用 `us-dossier` 命令：

```bash
# 基本用法（默认仅链接）
us-dossier build AAPL

# 全量下载模式
us-dossier build AAPL --download-mode full

# 完整选项示例
us-dossier build TSLA \
  --years 5 \
  --forms 10-K 10-Q 8-K "DEF 14A" 4 \
  --include-ir \
  --max-filings-per-form 20 \
  --download-mode links_only

# 更新现有档案（增量，遵循下载模式）
us-dossier update TSLA
us-dossier update TSLA --download-mode full

# 检查状态
us-dossier status TSLA

# 列出带过滤的文件
us-dossier list TSLA --form "10-K"
us-dossier list AAPL --since 2024-01-01

# 自定义工作区位置
us-dossier build MSFT --workspace ~/my-research
```

### 参数说明

#### `build_dossier()` / `update_dossier()`

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `ticker` | str | **必需** | 股票代码（如 "TSLA"） |
| `years` | int | 3 | 获取的历史数据年数 |
| `forms` | list | `["10-K", "10-Q", "8-K", "DEF 14A", "4"]` | 包含的 SEC 表格类型 |
| `include_ir` | bool | True | 包含投资者关系材料 |
| `max_filings_per_form` | int | 50 | 每种表格类型的最大文件数 |
| `force_rebuild` | bool | False | 强制重新下载所有内容 |
| `normalize_level` | str | "light" | 标准化级别："none"、"light" 或 "deep" |
| `fetch_mode` | str | "http" | 获取模式："http" 或 "browser_fallback" |
| `download_mode` | str | "links_only" | 下载模式："links_only" 或 "full" |

### 下载模式使用场景

#### `links_only` 模式（默认 - 推荐用于大多数场景）

**适用场景：**
- 进行财务分析、尽职调查或研究任务
- 需要快速访问文件元数据和 SEC 在线查看链接
- 使用能通过 URL 读取文档的 AI 代理或 LLM
- 构建研究索引或目录
- 带宽或存储空间有限
- 希望更快执行（无下载等待时间）

**优势：**
- **即时结果**：无文件下载延迟
- **零存储**：仅在本地存储元数据
- **始终最新**：SEC 在线查看器显示最新版本
- **低带宽**：无大文件传输
- **满足 95% 的分析场景**：大多数基于 AI/LLM 的分析可通过提供的 SEC URL 访问文档

#### `full` 模式（用于特殊需求）

**仅在以下情况使用：**
- 需要**离线访问**（无可用互联网连接）
- 执行需要原始 HTML/XBRL 解析的**自定义文档处理**
- **监管归档**要求本地文件存储
- 构建需要直接文件访问的**专业 ML 模型**
- 需要确保**文档不可变性**（防止远程更改）

**权衡：**
- 执行较慢（文件下载时间）
- 带宽使用量更高
- 需要大量存储空间
- 存在 SSL 错误或网络中断风险
- 文件可能随时间过时

#### 返回值

返回包含以下内容的字典：
- `dossier_path`：创建的档案目录路径
- `summary`：汇总统计，包括下载计数和最新日期
- `errors`：遇到的任何错误列表
- `quality_metrics`：完整性、新鲜度和可追溯性指标

## 输出结构

### 仅链接模式（默认）

在 `links_only` 模式下，档案仅包含元数据和 URL：

```
dossiers/{TICKER}/
├── manifest.json          # 带 SEC URL 和查看器链接的元数据
└── logs/
    └── run_*.log          # 执行日志
```

`manifest.json` 包含所有文件元数据：
- `url`：SEC 文档直接链接
- `metadata.viewer_url`：SEC 在线查看器 URL
- `metadata.raw_url`：原始文档 URL
- `parse_status`：设置为 "links_only"

### 全量下载模式

在 `full` 模式下，下载完整文件：

```
dossiers/{TICKER}/
├── manifest.json          # 完整元数据和审计跟踪
├── raw/
│   ├── sec/
│   │   ├── financial_reports/    # 10-K、10-Q 文件
│   │   ├── material_events/      # 8-K 文件
│   │   ├── proxy_statements/     # DEF 14A
│   │   └── insider_transactions/ # Form 4
│   └── ir/
│       ├── press/                # 新闻稿
│       └── presentations/        # 投资者演示
├── normalized/                   # 清理、结构化内容
│   ├── sec/
│   └── ir/
├── index/
│   └── documents.jsonl           # 用于 RAG 的可搜索块
└── logs/
    └── run_*.log                 # 执行日志
```

## 合规性

此技能严格遵守 SEC EDGAR 访问要求：

- **速率限制**：遵守每秒 10 次请求的最大限制（默认：2 rps）
- **User-Agent**：在 User-Agent 标头中需要有效的联系信息
- **公平访问**：对 429/503 错误实施指数退避
- **无需认证**：仅访问公开可用的数据

## 示例

### 示例 1：基本公司研究（仅链接）

```python
from us_company_dossier import build_dossier

# 为 Apple 创建综合档案（默认仅链接）
result = build_dossier(
    ticker="AAPL",
    years=5,
    forms=["10-K", "10-Q", "8-K"],
    download_mode="links_only",  # 默认模式
    include_ir=True
)

print(f"为 {result['company_info']['company_name']} 创建档案")
print(f"已索引 {len(result['artifacts'])} 个文件")

# 从 manifest 访问 SEC 链接
for artifact in result['artifacts']:
    if artifact['type'] == 'filing':
        print(f"{artifact['form']}: {artifact['metadata']['viewer_url']}")
```

### 示例 2：增量更新

```python
from us_company_dossier import update_dossier

# 仅获取自上次运行以来的新文件
result = update_dossier(ticker="MSFT")
if result['summary']['downloaded_count'] > 0:
    print(f"已更新 MSFT 档案，新增 {result['summary']['downloaded_count']} 个文档")
```

### 示例 3：全量下载模式（用于离线访问）

```python
from us_company_dossier import build_dossier

# 下载文件用于离线分析
result = build_dossier(
    ticker="TSLA",
    years=2,
    download_mode="full",  # 下载完整文件
    normalize_level="light"
)

print(f"已下载 {result['summary']['downloaded_count']} 个文件")
print(f"档案大小：{result['summary'].get('total_bytes', 0) / 1024 / 1024:.2f} MB")
```

### 示例 4：RAG 集成（全量模式）

```python
import json

# 加载索引用于检索（仅在全量模式可用）
with open("dossiers/TSLA/index/documents.jsonl", "r") as f:
    chunks = [json.loads(line) for line in f]

# 查找关于竞争的块
competition_chunks = [
    chunk for chunk in chunks 
    if "competition" in chunk.get("text", "").lower()
]

for chunk in competition_chunks[:3]:
    print(f"来源：{chunk['source_url']}")
    print(f"文本：{chunk['text'][:200]}...")
    print("---")
```

## 质量指标

每次运行都会生成质量指标以确保数据可靠性：

- **完整性**：验证是否存在最近所需的文件
- **新鲜度**：报告数据的时效性
- **可追溯性**：确保每条数据都可以追溯到其来源

## 限制

- 不处理需要付费或登录的内容
- PDF 解析可能在复杂布局上失败（默认无 OCR）
- 仅在 HTTP 失败时为 IR 站点启用浏览器回退
- 仅限于有 SEC 文件的美国上市公司

## 依赖

- Python 3.8+
- 核心依赖：requests、beautifulsoup4、lxml、html2text、tenacity、pydantic、markdownify、pdfminer.six
- 可选：playwright（用于浏览器回退模式）

使用 `pip install -e .` 自动安装依赖

浏览器回退支持（可选）：
```bash
pip install playwright
playwright install chromium
```

## 支持

如有问题或功能请求，请查看 OpenClaw 文档或社区论坛。
