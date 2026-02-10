# 美国上市公司档案技能

[English](SKILL.md) | **中文**

本技能将 OpenClaw 转变为"美国公司研究助手"，自动为美国上市公司构建全面的公司档案。

## 概述

给定美国股票代码（或公司名称），本技能可以：
- 自动获取 SEC EDGAR 文件元数据（10-K、10-Q、8-K、DEF 14A、Form 4）
- **默认模式**：提供 SEC 在线查看链接，无需下载文件（快速、高效）
- **完整模式**：下载完整文件用于离线分析（仅在特定需求时使用）
- 抓取投资者关系材料（新闻稿、演示文稿）
- 创建结构化、可审计、可增量更新的档案
- 生成标准化文本和分块索引用于 RAG 检索（仅完整模式）

## 核心特性

### 下载模式
- **`links_only`（默认）**：快速的仅元数据模式
  - 为所有文件生成 SEC 在线查看器链接
  - 无需文件下载 - 零带宽和存储开销
  - 适用于研究、分析和 AI 辅助工作流
  - 满足 95% 的使用场景
- **`full`**：完整文件下载模式
  - 下载所有文档用于离线访问
  - 支持自定义文档处理和归档
  - 适用于特殊用例（参见使用场景）

### 数据源
- **SEC EDGAR**（必需）：使用官方 SEC 公共数据 API
  - Submissions API 获取文件元数据
  - 根据模式直接链接或下载文档
  - XBRL 公司事实数据获取结构化财务数据
- **投资者关系**（可选）：HTTP 抓取新闻稿和演示文稿
  - 强制执行域名白名单以确保安全
  - 针对难以抓取的 IR 网站提供浏览器回退方案

### 输出结构

**仅链接模式**（默认 - 轻量级）：
```
dossiers/{TICKER}/
├── manifest.json          # 包含 SEC URL 和查看器链接的元数据
└── logs/                  # 执行日志
```

**完整下载模式**（明确需要时）：
```
dossiers/{TICKER}/
├── manifest.json          # 完整审计跟踪
├── raw/
│   ├── sec/
│   │   ├── financial_reports/    # 10-K, 10-Q
│   │   ├── material_events/      # 8-K
│   │   ├── proxy_statements/     # DEF 14A
│   │   └── insider_transactions/ # Form 4
│   └── ir/                        # 投资者关系材料
├── normalized/                    # 清理后的结构化内容
├── index/                         # RAG 就绪分块
│   └── documents.jsonl
└── logs/                          # 执行日志
```

### 合规性与安全性
- **SEC 公平访问**：严格的速率限制（≤10 请求/秒）
- **正确的 User-Agent**：需要配置联系信息
- **增量更新**：避免冗余下载
- **域名白名单**：IR 抓取仅限于已批准的域名

## 安装

### 快速安装（推荐）

作为系统命令安装，可从任何位置轻松访问：

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

### 替代方案：直接使用（无需安装）

如果不想安装，仍可以直接使用 CLI：

```bash
python /path/to/us-company-dossier-skill/cli.py build --ticker AAPL
```

## 使用方法

### 使用场景

#### 何时使用 `links_only` 模式（默认 - 推荐）
- **财务分析和研究**：通过 SEC 在线查看器阅读文件
- **AI/LLM 工作流**：智能体可以通过提供的 URL 访问文档
- **快速公司概览**：快速获取元数据，无需下载延迟
- **存储受限环境**：无需本地文件存储
- **合规检查**：验证文件存在性和日期
- **大多数分析场景**：约 95% 的场景不需要本地文件

#### 何时使用 `full` 模式（仅特殊需求）
- **离线访问**：分析期间无互联网连接
- **自定义文档处理**：需要原始 HTML/XBRL 解析
- **监管归档**：法律要求维护本地副本
- **ML 模型训练**：专用模型的直接文件访问
- **文档不变性**：防止源文档的远程更改

### 从 OpenClaw 使用

安装后，使用简单的命令格式：

```python
# 默认：仅链接模式（快速、高效）
exec("us-dossier build TSLA --years 3")

# 完整下载模式（仅在特定需要时）
exec("us-dossier build TSLA --years 3 --download-mode full")

# 使用自定义工作空间
exec("us-dossier build AAPL --workspace /path/to/workspace")
```

### 命令行界面

安装后，可从任何目录使用 `us-dossier`：

```bash
# 基本用法（仅链接 - 默认）
us-dossier build AAPL

# 完整下载模式
us-dossier build AAPL --download-mode full

# 带所有选项的仅链接模式
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

# 使用过滤器列出文件
us-dossier list TSLA --form "10-K"
us-dossier list AAPL --since 2024-01-01

# 自定义工作空间位置
us-dossier build MSFT --workspace ~/my-research
```

## 配置

关键配置选项（通过环境变量或配置文件设置）：

- `SEC_USER_AGENT`：必需的联系信息（例如："ResearchBot/1.0 (email@example.com)"）
- `SEC_RPS_LIMIT`：请求速率限制（默认：3，最大：10）
- `DOSSIER_ROOT`：档案基础目录（默认：./dossiers）
- `DOMAIN_ALLOWLIST`：允许的 IR 域名，逗号分隔
- `IR_BASE_URL_MAP`：股票代码到 IR 主页 URL 的 JSON 映射

## 质量指标

每次运行输出全面的质量指标：
- **完整性**：最近必需文件的覆盖率
- **新鲜度**：自上次更新以来的天数、最新文件日期
- **可追溯性**：100% 文件清单覆盖率，包含完整来源

## 依赖项

- Python 3.8+
- 核心：requests、beautifulsoup4、lxml、html2text、tenacity、pydantic、markdownify、pdfminer.six
- 可选：playwright（用于浏览器回退模式）

依赖项会通过 `pip install -e .` 自动安装

浏览器回退支持（可选）：
```bash
pip install playwright
playwright install chromium
```

## 示例

参见 `demo.py` 获取完整使用示例。
