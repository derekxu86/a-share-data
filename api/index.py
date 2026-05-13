from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ================= 1. 行情层 =================
async def fetch_tencent_quote(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://qt.gtimg.cn/q={prefix}{symbol}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code == 200 and 'v_' in r.text:
            parts = r.text.split('~')
            if len(parts) > 3:
                return {
                    "symbol": symbol,
                    "name": parts[1],
                    "price": float(parts[3]),
                    "change_pct": float(parts[32]),
                    "source": "腾讯财经",
                    "data_status": "real"
                }
    return None

@app.get("/api/market/quote")
async def get_quote(symbol: str):
    res = await fetch_tencent_quote(symbol)
    if res: return res
    raise HTTPException(status_code=404, detail="行情源失效")

# ================= 2. 搜索接口 =================
@app.get("/api/search/stocks")
async def search_stocks(q: str):
    url = f"https://smartbox.gtimg.cn/s3/?v=2&q={q}&t=all"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        match = re.search(r'v_hint="(.*)"', r.text)
        if not match: return {"items": []}
        raw = match.group(1).split('^')
        items = []
        for row in raw:
            p = row.split('~')
            if len(p) > 2:
                items.append({"symbol": p[1], "name": p[2], "py": p[3], "market": p[0].upper()})
        return {"items": items[:12]}

# ================= 3. 新闻层 =================
@app.get("/api/news/stock")
async def get_news(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://finance.pae.baidu.com/vapi/v1/getnewsinfo?code={prefix}{symbol}&rn=8"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            items = data.get('Result', {}).get('list', [])
            return {
                "symbol": symbol,
                "items": [{"title": i['title'], "source": i['source'], "date": i['time'], "url": i.get('url','')} for i in items],
                "source": "百度股市通",
                "data_status": "real"
            }
        except:
            return {"items": [], "source": "API Error", "data_status": "fallback", "note": "新闻获取失败"}

# ================= 4. 公告层 =================
@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://proxy.finance.qq.com/ifzq/appnews/app/news/list/symbol?symbol={prefix}{symbol}&type=2&page=1&limit=8"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            rows = data.get('data', {}).get('news', [])
            return {
                "symbol": symbol,
                "items": [{
                    "title": x.get('title'),
                    "type": "公司公告",
                    "date": x.get('publish_time'),
                    "url": x.get('url'),
                    "summary": x.get('desc') or x.get('title')
                } for x in rows],
                "source": "腾讯财经",
                "data_status": "real"
            }
        except:
             return {"items": [], "source": "Fallback", "data_status": "fallback", "note": "公告暂无数据"}

# ================= 5. 研报层 (Fallback 占位) =================
@app.get("/api/research/reports")
async def get_reports(symbol: str):
    # 暂时返回占位数据，确保前端不报错
    return {
        "symbol": symbol,
        "reports": [],
        "forecasts": [],
        "source": "Python Placeholder",
        "data_status": "placeholder",
        "is_fallback": True,
        "note": "研报接口需要后续接入东财 PDF 或机构数据源。"
    }

# ================= 6. 信号层 (Fallback 占位) =================
@app.get("/api/signals/overview")
async def get_signals(symbol: str):
    return {
        "symbol": symbol,
        "money_flow": {"items": []},
        "sector_ranking": {"items": []},
        "source": "Python Placeholder",
        "data_status": "placeholder",
        "is_fallback": True,
        "note": "资金流和行业排名接口待完善。"
    }

# ================= 7. AI 总结层 =================
@app.post("/api/ai/conviction")
async def ai_conviction(request: Request):
    # 接收前端传来的 5 层数据
    try:
        payload = await request.json()
    except:
        payload = {}
        
    symbol = payload.get("symbol", "000000")
    
    # 这里可以后续加上 openai 的调用。目前返回 mock 数据供 UI 渲染雷达图
    import random
    score = random.randint(55, 85)
    return {
        "conviction_score": score,
        "view": "Watchlist" if score > 70 else "Neutral",
        "market_regime": "波动观察期",
        "factor_scores": {
            "quote_layer": random.randint(40, 80),
            "research_layer": random.randint(40, 80),
            "signal_layer": random.randint(40, 80),
            "news_layer": random.randint(40, 80),
            "announcement_layer": random.randint(40, 80),
        },
        "bull_case": [
            "前端与 FastAPI 后端已成功连通",
            "行情、新闻、公告已接入真实数据流"
        ],
        "bear_case": [
            "研报和信号层目前为占位数据",
            "未配置真实 OpenAI Key"
        ],
        "final_summary": f"A股代码 {symbol} 分析就绪。系统已从报错中恢复，可继续开发深层数据。",
        "risk_warning": "仅用于技术演示",
        "data_status": "ai-generated",
        "source": "Local Python Mock"
    }
