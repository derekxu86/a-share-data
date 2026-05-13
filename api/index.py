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

# 伪装得更像一个真实的浏览器
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

def get_client():
    return httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0)

# ================= 1. 行情层 =================
@app.get("/api/market/quote")
async def get_quote(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url_tencent = f"https://qt.gtimg.cn/q={prefix}{symbol}"
    async with get_client() as client:
        try:
            r = await client.get(url_tencent, headers=HEADERS)
            if r.status_code == 200 and 'v_' in r.text:
                parts = r.text.split('~')
                if len(parts) > 3:
                    return {
                        "symbol": symbol, "name": parts[1], "price": float(parts[3]),
                        "change_pct": float(parts[32]), "source": "腾讯财经", "data_status": "real"
                    }
        except Exception:
            pass
    raise HTTPException(status_code=404, detail="行情源失效")

# ================= 2. 搜索接口 =================
@app.get("/api/search/stocks")
async def search_stocks(q: str):
    url = f"https://smartbox.gtimg.cn/s3/?v=2&q={q}&t=all"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            try:
                raw_text = codecs.decode(r.text, 'unicode_escape')
            except:
                raw_text = r.text
            match = re.search(r'v_hint="(.*)"', raw_text)
            if not match: return {"items": []}
            raw = match.group(1).split('^')
            items = []
            for row in raw:
                p = row.split('~')
                if len(p) > 2:
                    items.append({"symbol": p[1], "name": p[2], "py": p[3], "market": p[0].upper()})
            return {"items": items[:12]}
        except:
            return {"items": []}

# ================= 3. 新闻层 =================
@app.get("/api/news/stock")
async def get_news(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    error_msg = ""
    
    # 百度股市通
    url_baidu = f"https://finance.pae.baidu.com/vapi/v1/getnewsinfo?code={prefix}{symbol}&rn=8"
    async with get_client() as client:
        try:
            r = await client.get(url_baidu, headers={'Referer': 'https://gupiao.baidu.com/', **HEADERS})
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and isinstance(data.get('Result'), dict):
                    items = data['Result'].get('list', [])
                    if items:
                        return {
                            "symbol": symbol,
                            "items": [{"title": i.get('title',''), "source": i.get('source','百度'), "date": i.get('time',''), "url": i.get('url','')} for i in items],
                            "source": "百度股市通", "data_status": "real"
                        }
            else:
                error_msg += f"[Baidu HTTP {r.status_code}] "
        except Exception as e:
            error_msg += f"[Baidu Err] "

    # 东方财富搜索 API
    url_east = f"https://search-api-web.eastmoney.com/search/jsonp?keyword={symbol}&pageIndex=1&pageSize=8"
    async with get_client() as client:
        try:
            r = await client.get(url_east, headers=HEADERS)
            # 使用 [\s\S]* 允许跨行匹配 JSON
            match = re.search(r'\{[\s\S]*\}', r.text)
            if match:
                data = json.loads(match.group(0))
                if isinstance(data, dict) and isinstance(data.get('result'), dict):
                    rows = data['result'].get('data', [])
                    if rows:
                        return {
                            "symbol": symbol,
                            "items": [{"title": x.get('title','').replace('<font color=red>','').replace('</font>',''), "source": x.get('source', '东财'), "date": x.get('date'), "url": x.get('url')} for x in rows],
                            "source": "东方财富", "data_status": "real"
                        }
            else:
                error_msg += f"[East NoMatch: {r.text[:50]}]"
        except Exception as e:
            error_msg += f"[East Err: {str(e)}]"

    return {"items": [], "source": "API Error", "data_status": "fallback", "note": f"抓取失败详情: {error_msg}"}

# ================= 4. 公告层 (改用最稳的东财直连接口) =================
@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    # 东方财富官方底层公告接口 (抗拦截能力强)
    url = f"https://np-anotice-stock.eastmoney.com/api/security/ann?page_size=8&page_index=1&ann_type=A&client_source=web&stock_list={symbol}"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://data.eastmoney.com/', **HEADERS})
            if r.status_code != 200:
                return {"items": [], "source": "HTTP Error", "data_status": "fallback", "note": f"HTTP状态码: {r.status_code}"}
                
            data = r.json()
            if isinstance(data, dict) and isinstance(data.get('data'), dict):
                rows = data['data'].get('list', [])
                if rows:
                    return {
                        "symbol": symbol,
                        "items": [{
                            "title": x.get('title'),
                            "type": x.get('ann_type_desc', '公司公告'),
                            "date": x.get('notice_date')[:10] if x.get('notice_date') else '',
                            "url": f"https://data.eastmoney.com/notices/detail/{symbol}/{x.get('art_code')}.html" if x.get('art_code') else '',
                            "summary": x.get('title')
                        } for x in rows],
                        "source": "东方财富数据源", "data_status": "real"
                    }
            # 如果解析失败，把服务器到底回了啥打印出来
            return {"items": [], "source": "Data Error", "data_status": "fallback", "note": f"异常返回体: {str(data)[:80]}"}
        except Exception as e:
             return {"items": [], "source": "Code Error", "data_status": "fallback", "note": f"解析异常: {str(e)}"}

# ================= 5 & 6. 研报与信号层 (占位) =================
@app.get("/api/research/reports")
async def get_reports(symbol: str):
    return {"symbol": symbol, "reports": [], "forecasts": [], "source": "Python Placeholder", "data_status": "placeholder", "is_fallback": True, "note": "研报接口需要后续接入东财 PDF 或机构数据源。"}

@app.get("/api/signals/overview")
async def get_signals(symbol: str):
    return {"symbol": symbol, "money_flow": {"items": []}, "sector_ranking": {"items": []}, "source": "Python Placeholder", "data_status": "placeholder", "is_fallback": True, "note": "资金流和行业排名接口待完善。"}

# ================= 7. AI 总结层 =================
@app.post("/api/ai/conviction")
async def ai_conviction(request: Request):
    try:
        payload = await request.json()
    except:
        payload = {}
    symbol = payload.get("symbol", "000000")
    
    import random
    score = random.randint(55, 85)
    return {
        "conviction_score": score,
        "view": "Watchlist" if score > 70 else "Neutral",
        "market_regime": "波动观察期",
        "factor_scores": {
            "quote_layer": random.randint(40, 80), "research_layer": random.randint(40, 80),
            "signal_layer": random.randint(40, 80), "news_layer": random.randint(40, 80),
            "announcement_layer": random.randint(40, 80),
        },
        "bull_case": ["东财直连公告源已部署", "多行 JSONP 解析器修复完成"],
        "bear_case": ["若海外 IP 持续被风控，建议挂载代理"],
        "final_summary": f"A股代码 {symbol} 分析就绪。系统已实装异常透传机制，任何拦截都将在界面上明文显示。",
        "risk_warning": "仅用于技术演示",
        "data_status": "ai-generated", "source": "Local Python Mock"
    }
