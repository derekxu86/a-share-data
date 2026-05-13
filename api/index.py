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
    'Accept': 'application/json, text/plain, */*'
}

def get_client():
    return httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0)

# ================= 1. 行情层 =================
@app.get("/api/market/quote")
async def get_quote(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    
    # 首选：腾讯财经
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

    # 备选：新浪财经
    url_sina = f"https://hq.sinajs.cn/list={prefix}{symbol}"
    async with get_client() as client:
        try:
            r = await client.get(url_sina, headers={'Referer': 'https://finance.sina.com.cn/', **HEADERS})
            if r.status_code == 200 and '=' in r.text:
                data = re.search(r'="(.*)"', r.text).group(1).split(',')
                if len(data) > 3:
                    price = float(data[3])
                    prev_close = float(data[2])
                    change = ((price - prev_close) / prev_close) * 100 if prev_close else 0
                    return {
                        "symbol": symbol, "name": data[0], "price": price,
                        "change_pct": round(change, 2), "source": "新浪财经", "data_status": "real"
                    }
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="行情源失效")

# ================= 2. 搜索接口 (已修复 Unicode 乱码) =================
@app.get("/api/search/stocks")
async def search_stocks(q: str):
    url = f"https://smartbox.gtimg.cn/s3/?v=2&q={q}&t=all"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            # 强制解码 Unicode 逃逸字符 (例如 \u91d1\u8fbe\u5a01 -> 金达威)
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

# ================= 3. 新闻层 (已修复 NoneType 报错) =================
@app.get("/api/news/stock")
async def get_news(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    error_msg = ""
    
    # 首选：百度股市通
    url_baidu = f"https://finance.pae.baidu.com/vapi/v1/getnewsinfo?code={prefix}{symbol}&rn=8"
    async with get_client() as client:
        try:
            r = await client.get(url_baidu, headers={'Referer': 'https://gupiao.baidu.com/', **HEADERS})
            data = r.json()
            # 严格类型检查，防止 NoneType .get() 报错
            result_node = data.get('Result')
            if isinstance(result_node, dict):
                items = result_node.get('list', [])
                if items:
                    return {
                        "symbol": symbol,
                        "items": [{"title": i.get('title',''), "source": i.get('source','百度股市通'), "date": i.get('time',''), "url": i.get('url','')} for i in items],
                        "source": "百度股市通",
                        "data_status": "real"
                    }
        except Exception as e:
            error_msg += f"Baidu err: {str(e)}"
            
    # 备选：东方财富搜索 API
    url_east = f"https://search-api-web.eastmoney.com/search/jsonp?keyword={symbol}&pageIndex=1&pageSize=8"
    async with get_client() as client:
        try:
            r = await client.get(url_east, headers=HEADERS)
            match = re.search(r'\{.*\}', r.text)
            if match:
                data = json.loads(match.group(0))
                # 严格类型检查
                result_node = data.get('result')
                if isinstance(result_node, dict):
                    rows = result_node.get('data', [])
                    if rows:
                        return {
                            "symbol": symbol,
                            "items": [{"title": x.get('title','').replace('<font color=red>','').replace('</font>',''), "source": x.get('source', '东方财富'), "date": x.get('date'), "url": x.get('url')} for x in rows],
                            "source": "东方财富 API",
                            "data_status": "real"
                        }
        except Exception as e:
            error_msg += f" | East err: {str(e)}"

    return {"items": [], "source": "API Error", "data_status": "fallback", "note": f"新闻数据结构异常或被拦截: {error_msg}"}

# ================= 4. 公告层 (已修复 str 报错) =================
@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://proxy.finance.qq.com/ifzq/appnews/app/news/list/symbol?symbol={prefix}{symbol}&type=2&page=1&limit=8"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            data = r.json()
            # 严格类型检查，防止 data 节点返回的是一个字符串报错
            data_node = data.get('data')
            if isinstance(data_node, dict):
                rows = data_node.get('news', [])
                if rows:
                    return {
                        "symbol": symbol,
                        "items": [{
                            "title": x.get('title'), "type": "公司公告", "date": x.get('publish_time'),
                            "url": x.get('url'), "summary": x.get('desc') or x.get('title')
                        } for x in rows],
                        "source": "腾讯财经", "data_status": "real"
                    }
            return {"items": [], "source": "Fallback", "data_status": "fallback", "note": f"接口未返回标准格式，可能被软拦截。原始返回类型: {type(data_node).__name__}"}
        except Exception as e:
             return {"items": [], "source": "Fallback", "data_status": "fallback", "note": f"腾讯公告解析超时或失败: {str(e)}"}

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
        "bull_case": ["前端与 FastAPI 后端连通测试成功", "安全字典解析已部署"],
        "bear_case": ["研报和信号数据暂时使用占位符", "海外节点高频访问可能导致降级"],
        "final_summary": f"A股代码 {symbol} 分析就绪。搜索乱码与层级崩溃异常已修复。",
        "risk_warning": "仅用于技术演示",
        "data_status": "ai-generated", "source": "Local Python Mock"
    }
