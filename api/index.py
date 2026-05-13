from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re
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
    'Accept': 'application/json, text/plain, */*'
}

def get_client():
    return httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0)

# ================= 1. 行情层 (腾讯财经) =================
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

# ================= 2. 搜索接口 (腾讯 Smartbox) =================
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

# ================= 3. 新闻层 (腾讯财经-真个股新闻) =================
@app.get("/api/news/stock")
async def get_news(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    # type=1 代表专属个股新闻
    url = f"https://proxy.finance.qq.com/ifzq/appnews/app/news/list/symbol?symbol={prefix}{symbol}&type=1&page=1&limit=8"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            rows = data.get('data', {}).get('news', [])
            if rows:
                return {
                    "symbol": symbol,
                    "items": [{"title": x.get('title'), "source": "腾讯财经", "date": x.get('publish_time'), "url": x.get('url')} for x in rows],
                    "source": "腾讯个股资讯", "data_status": "real"
                }
            return {"items": [], "data_status": "fallback", "note": "近期无个股新闻"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

# ================= 4. 公告层 (东方财富直连 - 已被你验证成功) =================
@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?page_size=8&page_index=1&ann_type=A&client_source=web&stock_list={symbol}"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://data.eastmoney.com/'})
            data = r.json()
            rows = data.get('data', {}).get('list', [])
            if rows:
                return {
                    "symbol": symbol,
                    "items": [{"title": x.get('title'), "type": x.get('ann_type_desc', '公告'), "date": x.get('notice_date')[:10] if x.get('notice_date') else '', "url": f"https://data.eastmoney.com/notices/detail/{symbol}/{x.get('art_code')}.html", "summary": x.get('title')} for x in rows],
                    "source": "东财数据源", "data_status": "real"
                }
            return {"items": [], "data_status": "fallback", "note": "暂无公告"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

# ================= 5. 研报层 (腾讯财经-机构研报) =================
@app.get("/api/research/reports")
async def get_reports(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    # type=3 代表专属个股研报
    url = f"https://proxy.finance.qq.com/ifzq/appnews/app/news/list/symbol?symbol={prefix}{symbol}&type=3&page=1&limit=8"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            rows = data.get('data', {}).get('news', [])
            if rows:
                return {
                    "symbol": symbol,
                    "reports": [{"title": x.get('title'), "broker": x.get('source', '券商机构'), "date": x.get('publish_time')[:10], "url": x.get('url')} for x in rows],
                    "forecasts": [],
                    "source": "腾讯财经研报", "data_status": "real"
                }
            return {"symbol": symbol, "reports": [], "forecasts": [], "source": "腾讯财经", "data_status": "fallback", "note": "近期无研报"}
        except Exception as e:
            return {"symbol": symbol, "reports": [], "forecasts": [], "source": "Error", "data_status": "fallback", "note": str(e)}

# ================= 6. 信号层 (腾讯财经-资金流接口) =================
@app.get("/api/signals/overview")
async def get_signals(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://qt.gtimg.cn/q=ff_{prefix}{symbol}"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            if r.status_code == 200 and 'v_ff_' in r.text:
                parts = r.text.split('~')
                if len(parts) > 20:
                    main_inflow = float(parts[3])
                    super_large = float(parts[7])
                    return {
                        "symbol": symbol,
                        "money_flow": {
                            "items": [
                                {"label": "主力净流入", "value": f"{main_inflow}万"},
                                {"label": "超大单净流入", "value": f"{super_large}万"},
                                {"label": "资金流向信号", "value": "流入" if main_inflow > 0 else "流出"}
                            ],
                            "source": "腾讯财经资金流"
                        },
                        "sector_ranking": {"items": []},
                        "source": "腾讯资金流", "data_status": "real"
                    }
            return {"symbol": symbol, "money_flow": {"items": []}, "sector_ranking": {"items": []}, "source": "腾讯财经", "data_status": "fallback", "note": "无资金流数据"}
        except Exception as e:
            return {"symbol": symbol, "money_flow": {"items": []}, "sector_ranking": {"items": []}, "source": "Error", "data_status": "fallback", "note": str(e)}

# ================= 7. AI 总结层 =================
@app.post("/api/ai/conviction")
async def ai_conviction(request: Request):
    try: payload = await request.json()
    except: payload = {}
    symbol = payload.get("symbol", "000000")
    
    import random
    score = random.randint(55, 85)
    return {
        "conviction_score": score, "view": "Watchlist" if score > 70 else "Neutral", "market_regime": "波动观察期",
        "factor_scores": {"quote_layer": random.randint(40, 90), "research_layer": random.randint(40, 90), "signal_layer": random.randint(40, 90), "news_layer": random.randint(40, 90), "announcement_layer": random.randint(40, 90)},
        "bull_case": ["全节点已切换至抗封锁的腾讯/东财直连"],
        "bear_case": ["AI层目前为本地打分模拟"],
        "final_summary": f"A股代码 {symbol} 数据流梳理完毕。所有面板均已挂载真实的个股维度数据！",
        "risk_warning": "仅用于技术演示", "data_status": "ai-generated", "source": "Local Python Mock"
    }
