# AI Conviction Engine - Vercel Stable Node Version

这是一个适合直接部署到 Vercel 的 A股 AI 投研决策引擎原型。

这个版本已经移除 Python / FastAPI / AkShare，改成 Vercel 原生 Node.js Serverless API，主要解决：

```text
This Serverless Function has crashed
FUNCTION_INVOCATION_FAILED
```

## 为什么改成 Node.js？

Vercel 对 Python 金融数据包依赖比较敏感，AkShare / pandas / Tushare / FastAPI 组合容易出现 build 或 runtime 问题。  
Node.js API 在 Vercel 上更稳定。

## 项目结构

```text
.
├── api/
│   ├── health.js
│   ├── _utils.js
│   ├── market/
│   │   ├── quote.js
│   │   └── kline.js
│   ├── research/
│   │   └── reports.js
│   ├── signals/
│   │   └── overview.js
│   ├── news/
│   │   ├── global.js
│   │   ├── latest.js
│   │   └── stock.js
│   ├── announcements/
│   │   └── stock.js
│   └── ai/
│       └── conviction.js
├── src/
├── index.html
├── package.json
├── vercel.json
└── .env.example
```

## Vercel Environment Variables

在 Vercel Project Settings → Environment Variables 添加：

```env
OPENAI_API_KEY=你的新OpenAI key
TUSHARE_TOKEN=你的Tushare token
FINNHUB_API_KEY=你的Finnhub key
OPENAI_MODEL=gpt-4o-mini
```

## API 测试

部署后先打开：

```text
https://你的域名.vercel.app/api/health
```

应该返回：

```json
{
  "name": "AI Conviction Engine",
  "status": "ok",
  "runtime": "vercel-node",
  "api": "stable"
}
```

## 已接入

| Layer | Endpoint | 数据源 |
|---|---|---|
| 健康检查 | `/api/health` | 本地 |
| 行情层 | `/api/market/quote?symbol=600519` | 东方财富 push2 + Tushare 增强 |
| K线层 | `/api/market/kline?symbol=600519` | Tushare daily |
| 信号层 | `/api/signals/overview?symbol=600519` | Tushare moneyflow |
| 研报层 | `/api/research/reports?symbol=600519` | Tushare forecast placeholder |
| 新闻层 | `/api/news/global` | Finnhub |
| 公告层 | `/api/announcements/stock?symbol=600519` | 占位 |
| AI总结 | `/api/ai/conviction` | OpenAI |

## 注意

- 这个版本以“稳定部署”为优先。
- 没有 Python 依赖，不会再出现 Python Serverless crash。
- AkShare / mootdx 如果以后要做，建议单独放到 Railway / Render / VPS 后端。
- Vercel 只做前端 + 轻量 API。
- 本项目仅用于研究和教育演示，不构成投资建议。
