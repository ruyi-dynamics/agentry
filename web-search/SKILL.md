---
name: web-search
description: |
  开源 Web 搜索 — 使用 SearXNG 自托管搜索引擎（聚合 Google/Bing/DuckDuckGo/Brave 等），
  无需 API key，无限额。SearXNG 不可用时自动回退到 DuckDuckGo。

  TRIGGER when: 用户要求搜索网页、查找信息、搜索新闻，
  或其他 skill 需要搜索能力时。
  也适用于 "搜索XX"、"帮我查一下XX"、"最近有什么新闻" 等查询。
  可作为 tech-radar 等 skill 的搜索后端。
---

# 技能：Web Search

## 说明

使用 SearXNG 自托管搜索引擎，聚合多个搜索引擎结果，无需 API key，无速率限制。
SearXNG 通过 Docker 运行在 `localhost:8888`，不可用时自动回退到 DuckDuckGo。

依赖：
- Docker（运行 SearXNG 容器）
- `python3.11 -m pip install --user ddgs`（DuckDuckGo 回退）

## SearXNG 管理

```bash
# 启动 SearXNG
cd ~/agentry/web-search/searxng && docker compose up -d

# 停止 SearXNG
cd ~/agentry/web-search/searxng && docker compose down

# 查看日志
docker logs searxng

# 测试 API
curl "http://localhost:8888/search?q=test&format=json"
```

## 使用方式

### 命令行直接调用

```bash
# 基本搜索（默认使用 SearXNG）
python3.11 ~/agentry/web-search/scripts/search.py "搜索关键词"

# 指定结果数量
python3.11 ~/agentry/web-search/scripts/search.py "搜索关键词" -n 5

# JSON 输出（适合程序解析）
python3.11 ~/agentry/web-search/scripts/search.py "搜索关键词" --json

# 指定搜索引擎
python3.11 ~/agentry/web-search/scripts/search.py "搜索关键词" -e "google,bing"

# 使用 DuckDuckGo 后端
python3.11 ~/agentry/web-search/scripts/search.py "搜索关键词" -b ddg
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `query` | 搜索关键词（必填） | — |
| `-n, --max-results` | 最大结果数 | 10 |
| `-b, --backend` | 搜索后端 (`searxng`, `ddg`, `auto`) | `searxng` |
| `-l, --lang` | 语言 | `auto` |
| `-r, --region` | 搜索区域（DDG 用） | `wt-wt`（全球） |
| `-e, --engines` | SearXNG 引擎（逗号分隔） | 全部 |
| `--json` | JSON 输出格式 | 否 |

## 代理配置

SearXNG 运行在本地 Docker 中，直连不走代理。
DuckDuckGo 回退通过 SOCKS5 代理（Clash 默认 `socks5://127.0.0.1:7897`）。

## 在其他 Skill 中使用

```bash
# 替代 WebSearch
python3.11 ~/agentry/web-search/scripts/search.py "LLM leaderboard 2026" -n 5 --json

# 指定引擎
python3.11 ~/agentry/web-search/scripts/search.py "query" -e "google,arxiv" --json

# 解析 JSON 结果
results=$(python3.11 ~/agentry/web-search/scripts/search.py "query" --json)
echo "$results" | python3.11 -c "import sys,json; [print(r['title'],r['href']) for r in json.load(sys.stdin)]"
```

## SearXNG 配置

配置文件位于 `~/agentry/web-search/searxng/settings.yml`：
- 启用的搜索引擎：google, bing, duckduckgo, brave, arxiv, github 等
- 输出格式：html, json, csv, rss
- 无速率限制（limiter: false）

## 注意事项

- SearXNG 聚合多个搜索引擎，结果质量优于单一 DuckDuckGo
- Docker 容器需要随系统启动（已配置 `restart: unless-stopped`）
- 如 Docker 未运行，脚本自动回退到 DuckDuckGo
- JSON 格式需要在 settings.yml 的 `search.formats` 中启用
