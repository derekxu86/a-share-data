# AI Conviction Engine

A股 AI 投研决策引擎原型。  
结构参考：行情层、研报层、信号层、新闻层、公告层、AI 总结层。

> 本项目仅用于学习、研究和产品原型展示，不构成任何投资建议。

## Vercel 友好结构

```text
ai-conviction-engine/
├── api/
│   ├── index.py              Vercel Python / FastAPI 入口
│   └── app/
│       ├── config.py
│       ├── routers/
│       ├── services/
│       └── utils/
├── src/                      React 前端
├── index.html
├── package.json
├── requirements.txt          Python dependencies
├── vercel.json
├── vite.config.ts
└── .env.example
```

## 数据层

| Layer | 功能 | 默认数据源 |
|---|---|---|
| 行情层 | K线、报价、估值、盘口 | AkShare + Tushare 增强 |
| 研报层 | 研报列表、PDF、EPS预测 | AkShare / 东方财富思路 |
| 信号层 | 北向资金、资金流、龙虎榜、行业排名 | AkShare + Tushare 增强 |
| 新闻层 | 财经快讯、个股新闻、全球新闻 | AkShare + Finnhub |
| 公告层 | 公司公告、财报、交易所公告 | 巨潮 / AkShare 思路 |
| AI总结层 | Conviction Score、Bull/Bear Case | OpenAI |

## Vercel 部署

### 1. 推送到 GitHub

```bash
git init
git add .
git commit -m "Initial AI Conviction Engine"
git branch -M main
git remote add origin https://github.com/你的用户名/ai-conviction-engine.git
git push -u origin main
```

### 2. 在 Vercel 导入 GitHub repo

Framework Preset 选择：

```text
Vite
```

Vercel 会使用：

```text
Build Command: npm run build
Output Directory: dist
```

### 3. 在 Vercel 添加 Environment Variables

不要把真实 key 写进 GitHub。  
在 Vercel Project Settings → Environment Variables 添加：

```env
OPENAI_API_KEY=你的新OpenAI key
TUSHARE_TOKEN=你的Tushare token
FINNHUB_API_KEY=你的Finnhub key
OPENAI_MODEL=gpt-4.1-mini
```

可选：

```env
ALLOWED_ORIGINS=*
```

生产环境建议改成你的 Vercel 域名，例如：

```env
ALLOWED_ORIGINS=https://your-project.vercel.app
```

### 4. 测试 API

部署后访问：

```text
https://你的域名.vercel.app/api/health
```

应该返回：

```json
{
  "name": "AI Conviction Engine",
  "status": "ok",
  "runtime": "vercel-python"
}
```

## 本地运行

### 前端

```bash
npm install
npm run dev
```

### 后端本地测试

```bash
pip install -r requirements.txt
uvicorn api.index:app --reload --port 8000
```

本地如果前端要连本地后端，可以建 `.env.local`：

```env
VITE_API_BASE=http://localhost:8000
```

## 主要 API

```http
GET  /api/health
GET  /api/market/quote?symbol=600519
GET  /api/market/kline?symbol=600519&period=daily

GET  /api/research/reports?symbol=600519
GET  /api/signals/overview?symbol=600519
GET  /api/news/stock?symbol=600519
GET  /api/news/global
GET  /api/announcements/stock?symbol=600519

POST /api/ai/conviction
```

## Key 用途

| Key | 用途 | 是否必须 |
|---|---|---|
| `OPENAI_API_KEY` | AI总结、Conviction Score、Bull/Bear Case | 必须 |
| `TUSHARE_TOKEN` | A股估值、资金流、基础数据增强 | 建议 |
| `FINNHUB_API_KEY` | 全球新闻、后续美股/全球市场扩展 | 可选 |

## 注意

如果 key 曾经出现在聊天、截图、公开仓库或前端代码中，请立即 rotate。  
本项目不做自动交易、不做下单、不做荐股，只做研究和决策辅助。
