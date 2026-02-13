# 美国上市公司档案技能

[English](SKILL.md) | **中文**

本技能将 OpenClaw 转变为"美国公司研究助手"，自动为美国上市公司构建全面的元数据档案。

## 概述

给定美国股票代码（或公司名称），本技能可以：
- 自动获取 SEC EDGAR 文件元数据（10-K、10-Q、8-K、DEF 14A、Form 4）
- 提供所有文件的 SEC 在线查看链接（快速、高效）
- 创建结构化、可审计的 manifest.json 文件
- 无需文件下载 - 零带宽和存储开销

## 核心特性

### 数据源
- **SEC EDGAR**：使用官方 SEC 公共数据 API
  - Submissions API 获取文件元数据
  - 直接文档链接和 SEC 查看器 URL
  - XBRL 公司事实数据获取结构化财务数据

### 输出结构

```
dossiers/{TICKER}/
├── manifest.json          # 完整的文件元数据及 SEC 查看器链接
└── logs/                  # 执行日志
```

### 合规性与安全性
- **SEC 公平访问**：严格的速率限制（≤10 请求/秒）
- **正确的 User-Agent**：需要配置联系信息

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

### 从 OpenClaw 使用

安装后，使用简单的命令格式：

```python
# 构建公司档案
exec("us-dossier build TSLA --years 3")

# 使用自定义工作空间
exec("us-dossier build AAPL --workspace /path/to/workspace")
```

### 命令行界面

安装后，可从任何目录使用 `us-dossier`：

```bash
# 基本用法
us-dossier build AAPL

# 带所有选项
us-dossier build TSLA \
  --years 5 \
  --forms 10-K 10-Q 8-K "DEF 14A" 4 \
  --max-filings-per-form 20

# 更新现有档案（增量）
us-dossier update TSLA

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

## 质量指标

每次运行输出全面的质量指标：
- **完整性**：最近必需文件的覆盖率
- **新鲜度**：自上次更新以来的天数、最新文件日期
- **可追溯性**：100% 文件清单覆盖率，包含完整元数据

## 依赖项

- Python 3.8+
- 核心：requests、pydantic

依赖项会通过 `pip install -e .` 自动安装

## 示例

参见 `demo.py` 获取完整使用示例。
