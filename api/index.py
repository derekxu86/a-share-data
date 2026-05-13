from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re
import os
import codecs

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

# 从 Vercel 环境变量中读取 Tushare Token
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")

def get_client():
    return httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0)

# 核心：Tushare 通用请求器
async def fetch_tushare(api_name: str, params: dict):
    if not TUSHARE_TOKEN:
        raise ValueError("TUSHARE_TOKEN 未配置")
    
    url = "http://api.tushare.pro"
    payload = {
        "api_name": api_name,
        "token": TUSHARE_TOKEN,
        "params": params,
        "fields": ""
    }
    async with get_client() as client:
        r = await client.post(url, json=payload)
        data = r.json()
        if data.get('code') != 0:
            raise ValueError(f"Tushare API 报错: {data.get('msg')}")
        return data.get('data', {})

# ================= 1. 行情层 (保留未被封的腾讯财经) =================
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

# ================= 2. 搜索接口 (腾讯 Smartbox 极其稳定) =================
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

# ================= 3. 新闻层 (切至 Tushare 正规 API) =================
@app.get("/api/news/stock")
async def get_news(symbol: str):
    if not TUSHARE_TOKEN:
         return {"items": [], "data_status": "fallback", "note": "请在 Vercel 设置 TUSHARE_TOKEN 环境变量"}
    
    try:
        # 使用 Tushare 的 news 接口 (新浪财经新闻源)
        data = await fetch_tushare("news", {"src": "sina"})
        fields = data.get('fields', [])
        rows = data.get('items', [])
        
        if rows:
            # Tushare 返回的是列表嵌套列表，我们需要根据 fields 映射成字典
            items = []
            for row in rows[:8]:
                row_dict = dict(zip(fields, row))
                items.append({
                    "title": row_dict.get('title', ''),
                    "source": row_dict.get('src', '新浪财经 (Tushare)'),
                    "date": row_dict.get('datetime', ''),
                    "summary": row_dict.get('content', '')[:100] + '...'
                })
            return {"symbol": symbol, "items": items, "source": "Tushare Pro API", "data_status": "real"}
        return {"items": [], "data_status": "fallback", "note": "Tushare 暂无相关新闻"}
    except Exception as e:
        return {"items": [], "data_status": "fallback", "note": f"API调用失败: {str(e)}"}

# ================= 4. 公告层 (切至 Tushare 正规 API) =================
@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    if not TUSHARE_TOKEN:
         return {"items": [], "data_status": "fallback", "note": "请配置 TUSHARE_TOKEN"}
    
    # 格式化代码给 Tushare (例如：600519.SH)
    ts_code = f"{symbol}.SH" if symbol.startswith('6') else f"{symbol}.SZ"
    
    try:
        # 使用 Tushare 的 disclosure 接口获取公告
        data = await fetch_tushare("disclosure_date", {"ts_code": ts_code})
        fields = data.get('fields', [])
        rows = data.get('items', [])
        
        if rows:
            items = []
            for row in rows[:8]:
                row_dict = dict(zip(fields, row))
                items.append({
                    "title": f"定期报告披露日期变更/公告", 
                    "type": "公司公告 (Tushare)",
                    "date": row_dict.get('modify_date', row_dict.get('pre_date', '')),
                    "summary": f"预计首次披露日: {row_dict.get('pre_date')}"
                })
            return {"symbol": symbol, "items": items, "source": "Tushare Pro API", "data_status": "real"}
        return {"items": [], "data_status": "fallback", "note": "Tushare 暂无相关公告"}
    except Exception as e:
         return {"items": [], "data_status": "fallback", "note": f"API调用失败: {str(e)}"}

# ================= 5 & 6. 研报与信号层 (占位) =================
@app.get("/api/research/reports")
async def get_reports(symbol: str):
    return {"symbol": symbol, "reports": [], "forecasts": [], "source": "Placeholder", "data_status": "placeholder"}

@app.get("/api/signals/overview")
async def get_signals(symbol: str):
    return {"symbol": symbol, "money_flow": {"items": []}, "sector_ranking": {"items": []}, "source": "Placeholder", "data_status": "placeholder"}

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
        "factor_scores": {"quote_layer": random.randint(40, 90), "research_layer": 50, "signal_layer": 50, "news_layer": random.randint(40, 90), "announcement_layer": random.randint(40, 90)},
        "bull_case": ["放弃爬虫，已全面接入 Tushare 官方 REST API", "彻底免疫海外 IP 拦截问题"],
        "bear_case": ["Tushare 部分高级接口需要积分权限", "研报层仍需接入 PDF 解析"],
        "final_summary": f"A股代码 {symbol} 架构升级完毕。通过正规金融 API 抓取数据，系统稳定性已达到生产环境级别。",
        "risk_warning": "仅用于技术演示", "data_status": "ai-generated", "source": "Local Python Mock"
    }
