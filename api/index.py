from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re
import json
import codecs

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def get_client():
    return httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0)

@app.get("/api/market/quote")
async def get_quote(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    async with get_client() as client:
        try:
            r = await client.get(f"https://qt.gtimg.cn/q={prefix}{symbol}", headers=HEADERS)
            if r.status_code == 200 and 'v_' in r.text:
                p = r.text.split('~')
                if len(p) > 3:
                    return {"symbol": symbol, "name": p[1], "price": float(p[3]), "change_pct": float(p[32]), "source": "腾讯财经", "data_status": "real"}
        except: pass
    raise HTTPException(status_code=404, detail="行情获取失败")

@app.get("/api/search/stocks")
async def search_stocks(q: str):
    async with get_client() as client:
        try:
            r = await client.get(f"https://smartbox.gtimg.cn/s3/?v=2&q={q}&t=all", headers=HEADERS)
            try: raw = codecs.decode(r.text, 'unicode_escape')
            except: raw = r.text
            match = re.search(r'v_hint="(.*)"', raw)
            if not match: return {"items": []}
            items = []
            for row in match.group(1).split('^'):
                p = row.split('~')
                if len(p) > 2: items.append({"symbol": p[1], "name": p[2], "py": p[3], "market": p[0].upper()})
            return {"items": items[:12]}
        except: return {"items": []}

@app.get("/api/news/stock")
async def get_news(symbol: str):
    market = 1 if symbol.startswith('6') else 0
    url = f"https://np-webapp.eastmoney.com/api/Article/GetZixunList?code={symbol}&market={market}&pageIndex=1&pageSize=8"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://emwap.eastmoney.com/', **HEADERS})
            data = r.json()
            rows = data.get('data', {}).get('list', [])
            if rows:
                return {
                    "symbol": symbol,
                    "items": [{"title": x.get('title',''), "source": x.get('source','东财'), "date": x.get('showTime',''), "url": x.get('url','')} for x in rows],
                    "source": "东方财富移动端", "data_status": "real"
                }
            return {"items": [], "data_status": "fallback", "note": "暂无新闻"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?page_size=8&page_index=1&ann_type=A&client_source=web&stock_list={symbol}"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://data.eastmoney.com/', **HEADERS})
            data = r.json()
            rows = data.get('data', {}).get('list', [])
            if rows:
                return {
                    "symbol": symbol,
                    "items": [{"title": x.get('title'), "type": x.get('ann_type_desc', '公告'), "date": x.get('notice_date')[:10], "url": f"https://data.eastmoney.com/notices/detail/{symbol}/{x.get('art_code')}.html"} for x in rows],
                    "source": "东财数据源", "data_status": "real"
                }
            return {"items": [], "data_status": "fallback", "note": "暂无公告"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

@app.get("/api/research/reports")
async def get_reports(symbol: str):
    return {"symbol": symbol, "reports": [], "forecasts": [], "source": "Placeholder", "data_status": "placeholder"}

@app.get("/api/signals/overview")
async def get_signals(symbol: str):
    return {"symbol": symbol, "money_flow": {"items": []}, "sector_ranking": {"items": []}, "source": "Placeholder", "data_status": "placeholder"}

@app.post("/api/ai/conviction")
async def ai_conviction(request: Request):
    import random
    score = random.randint(55, 85)
    return {
        "conviction_score": score, "view": "Watchlist" if score > 70 else "Neutral", "market_regime": "波动观察期",
        "factor_scores": {"quote_layer": random.randint(40, 90), "research_layer": 50, "signal_layer": 50, "news_layer": random.randint(40, 90), "announcement_layer": random.randint(40, 90)},
        "bull_case": ["东财/腾讯/百度多源数据链已打通", "Unicode 乱码与防御性解析已实装"],
        "bear_case": ["研报层仍需接入 PDF 解析", "AI 层目前为本地模拟"],
        "final_summary": "系统运行正常。行情、新闻、公告已恢复真实数据流。",
        "risk_warning": "仅用于技术演示", "data_status": "ai-generated", "source": "Local Python Mock"
    }
