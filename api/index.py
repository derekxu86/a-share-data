from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re
import json
import codecs
import datetime

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

# JSONP 强力解析器
def parse_jsonp(text):
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try: return json.loads(match.group(0))
        except: pass
    return {}

# ================= 1. 行情层 (腾讯财经 - 稳定) =================
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

# ================= 2. 搜索接口 =================
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

# ================= 3. 新闻层 (新浪信息流 - 稳定无防爬) =================
@app.get("/api/news/stock")
async def get_news(symbol: str):
    url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k={symbol}&num=8&page=1"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://finance.sina.com.cn/'})
            data = r.json()
            rows = data.get('result', {}).get('data', [])
            if rows:
                items = []
                for x in rows:
                    ts = int(x.get('ctime', 0))
                    date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else ''
                    items.append({"title": x.get('title', ''), "source": "新浪财经", "date": date_str, "url": x.get('url', '')})
                return {"symbol": symbol, "items": items, "source": "新浪信息流API", "data_status": "real"}
            return {"items": [], "data_status": "fallback", "note": "新浪暂无该股新闻"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

# ================= 4. 公告层 (换回曾经成功过的东财底层API) =================
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
                    "source": "东方财富", "data_status": "real"
                }
            return {"items": [], "data_status": "fallback", "note": "暂无公告"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

# ================= 5. 研报层 (东财 ReportAPI) =================
@app.get("/api/research/reports")
async def get_reports(symbol: str):
    url = f"https://reportapi.eastmoney.com/report/list?pageSize=8&pageNo=1&qType=0&code={symbol}"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://data.eastmoney.com/report/'})
            data = parse_jsonp(r.text)
            rows = data.get('data', [])
            if rows:
                return {
                    "symbol": symbol,
                    "reports": [{"title": x.get('title', '研报'), "broker": x.get('orgSName', '机构'), "date": x.get('publishDate', '')[:10], "url": x.get('pdfUrl', '')} for x in rows],
                    "forecasts": [],
                    "source": "东方财富研报", "data_status": "real"
                }
            return {"symbol": symbol, "reports": [], "forecasts": [], "source": "东方财富", "data_status": "fallback", "note": "近期无研报"}
        except Exception as e:
            return {"symbol": symbol, "reports": [], "forecasts": [], "source": "Error", "data_status": "fallback", "note": str(e)}

# ================= 6. 信号层 (东财资金流 Push2His) =================
@app.get("/api/signals/overview")
async def get_signals(symbol: str):
    secid = f"1.{symbol}" if symbol.startswith('6') else f"0.{symbol}"
    url = f"https://push2his.eastmoney.com/api/qt/stock/fflow/kline/get?secid={secid}&klt=101&lmt=10&fields1=f1,f2,f3,f7&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://quote.eastmoney.com/'})
            data = r.json()
            klines = data.get('data', {}).get('klines', [])
            if klines:
                # 获取最新一天的资金流数据
                latest = klines[-1].split(',')
                main_inflow = float(latest[1])
                return {
                    "symbol": symbol,
                    "money_flow": {
                        "items": [
                            {"label": "主力净流入", "value": f"{main_inflow}万"},
                            {"label": "超大单净入", "value": f"{latest[4]}万"},
                            {"label": "资金流向信号", "value": "流入" if main_inflow > 0 else "流出"}
                        ],
                        "source": "东方财富资金流"
                    },
                    "sector_ranking": {"items": []},
                    "source": "东方财富", "data_status": "real"
                }
            return {"symbol": symbol, "money_flow": {"items": []}, "sector_ranking": {"items": []}, "source": "东方财富", "data_status": "fallback", "note": "无资金流数据"}
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
        "bull_case": ["五层真实数据通道已全部打通"],
        "bear_case": ["AI层目前为本地打分模拟"],
        "final_summary": f"A股代码 {symbol} 架构重构完成。研报、信号、公告全数归位，不再使用假数据占位。",
        "risk_warning": "仅用于技术演示", "data_status": "ai-generated", "source": "Local Python Mock"
    }
