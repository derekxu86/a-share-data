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


## Safe UI Fix

如果首页加载一下后黑屏，通常是前端渲染时某个 API 返回格式与预期不同。  
本版本已加入：

- ErrorBoundary，防止整页黑屏
- safeArray，防止 `bull_case.map is not a function`
- safeText / safeNumber，防止对象或空值直接渲染
- 更稳的 JSON fallback


## UI Upgrade v1

本版本修复：

- 搜索框支持代码、中文、拼音首字母
- 搜索框有下拉建议
- 研报层不再只显示空数组，会显示状态卡片
- 雷达六边形增加明显橙色填充、描边、网格线和点位
