# AI Conviction Engine - Vercel Single Function

这是适合 Vercel Hobby 免费版部署的版本。

## 为什么要合并 API？

Vercel Hobby 免费版限制：

```text
No more than 12 Serverless Functions
```

所以本版本把所有 API 合并进：

```text
api/index.js
```

这样 Vercel 只会创建 **1 个 Serverless Function**。

## 结构

```text
.
├── api/
│   └── index.js
├── src/
├── index.html
├── package.json
├── vercel.json
└── .env.example
```

## Vercel 环境变量

在 Vercel Project Settings → Environment Variables 添加：

```env
OPENAI_API_KEY=你的新OpenAI key
TUSHARE_TOKEN=你的Tushare token
FINNHUB_API_KEY=你的Finnhub key
OPENAI_MODEL=gpt-4o-mini
```

## 测试地址

部署后先打开：

```text
/api/health
```

然后测试：

```text
/api/market/quote?symbol=600519
/api/signals/overview?symbol=600519
/api/ai/conviction
```

## 已合并的接口

```text
GET  /api/health
GET  /api/market/quote?symbol=600519
GET  /api/market/kline?symbol=600519
GET  /api/research/reports?symbol=600519
GET  /api/signals/overview?symbol=600519
GET  /api/news/global
GET  /api/news/stock?symbol=600519
GET  /api/announcements/stock?symbol=600519
POST /api/ai/conviction
```

## 注意

本项目仅用于研究和教育演示，不构成投资建议。  
