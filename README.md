# AI Conviction Engine - A股数据源结构版

本版本按你提供的图中数据源重构，不再把 Tushare / Finnhub 作为核心源。

## 图中数据源

| 数据源 | 协议 | 是否需要 Key | Vercel Node 适配 |
|---|---|---|---|
| mootdx | TCP 7709 | 免费 | 不适合 Vercel，适合独立 Python 后端 |
| 腾讯财经 | HTTP | 免费 | 适合 |
| akshare | Python | 免费 | 不适合 Vercel Node，适合独立 Python 后端 |
| iwencai | REST API | 需 Key / Cookie | 后续接 |
| 东方财富 PDF | HTTP | 免费 | 适合 |
| 同花顺 | HTTP | 免费 | 部分适合 |
| 百度股市通 | HTTP | 免费 | 适合 |
| 巨潮 | HTTP | 免费 | 适合 |

## 当前 Vercel 版策略

Vercel Hobby 免费版最稳的是：

```text
前端 React
+
单个 Node Serverless Function
+
HTTP 数据源
```

所以当前版本：

- 行情层：东方财富 HTTP → 腾讯财经 HTTP → fallback
- 研报层：东方财富 PDF 结构预留 + fallback
- 信号层：同花顺/东方财富/百度股市通结构预留 + fallback
- 新闻层：腾讯财经/百度股市通结构预留 + fallback
- 公告层：巨潮结构预留 + fallback
- AI总结层：OpenAI

## 不在 Vercel 里直接跑的源

```text
mootdx
akshare
```

原因：

- `mootdx` 走 TCP 7709，适合 VPS / Railway / Render，不适合 Vercel Serverless
- `akshare` 是 Python 包，适合独立 Python 后端，不适合当前 Node 单函数版本

## 推荐最终架构

```text
Vercel:
- React frontend
- Node /api/index.js
- 东方财富 / 腾讯财经 / 百度股市通 / 巨潮 HTTP

Railway 或 Render:
- Python service
- mootdx
- akshare
```

## Environment Variables

Vercel 目前只必须要：

```env
OPENAI_API_KEY=你的OpenAI key
OPENAI_MODEL=gpt-4o-mini
```

可选：

```env
IWENCAI_KEY=
```

不再需要：

```env
TUSHARE_TOKEN
FINNHUB_API_KEY
```

## API

```text
GET  /api/health
GET  /api/market/quote?symbol=600519
GET  /api/market/kline?symbol=600519
GET  /api/research/reports?symbol=600519
GET  /api/signals/overview?symbol=600519
GET  /api/news/stock?symbol=600519
GET  /api/announcements/stock?symbol=600519
POST /api/ai/conviction
```

## 注意

本项目仅用于研究和教育演示，不构成投资建议。


## A-stock sources v2

本版本修复：

- 搜索支持任意 6 位 A股代码，例如 `002626`
- 内置股票池新增 `002626 金达威`
- 回车可直接搜索 6 位代码
- 每个模块增加数据状态标签：
  - 绿色：真实数据
  - 黄色：Fallback占位
  - 蓝色：接口预留
  - 紫色：AI生成


## v3 Real Search

本版本修复：

- 搜索框调用 `/api/search/stocks?q=`
- 优先使用东方财富全市场股票列表
- 支持代码、中文名、拼音首字母
- 如果东方财富股票列表不可用，才 fallback 到本地小股票池
- 行情层增加新浪财经作为第三行情源：东方财富 → 腾讯财经 → 新浪财经 → fallback
- 状态标签继续显示真实数据 / fallback / 接口预留
