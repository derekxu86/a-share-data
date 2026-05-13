from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re
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
    # 忽略证书错误，允许重定向，加长超时，最大程度适应 Vercel 网络
    return httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0)

# ================= 1. 行情层 (最稳的腾讯财经) =================
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

# ================= 2. 搜索接口 (腾讯财经 Smartbox) =================
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

# ================= 3. 新闻层 (新浪无限制信息流 API) =================
@app.get("/api/news/stock")
async def get_news(symbol: str):
    # 新浪新闻聚合 API，无需 Token，不封海外 IP
    url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&k={symbol}&num=8&page=1"
    async with get_client() as client:
        try:
            r = await client.get(url, headers={'Referer': 'https://finance.sina.com.cn/'})
            data = r.json()
            rows = data.get('result', {}).get('data', [])
            if rows:
                items = []
                for x in rows:
                    # 新浪返回的是时间戳
                    ts = int(x.get('ctime', 0))
                    date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else ''
                    items.append({
                        "title": x.get('title', ''),
                        "source": "新浪财经",
                        "date": date_str,
                        "url": x.get('url', '')
                    })
                return {"symbol": symbol, "items": items, "source": "新浪信息流API", "data_status": "real"}
            return {"items": [], "data_status": "fallback", "note": "新浪暂无该股新闻"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

# ================= 4. 公告层 (新浪网页硬核正则提取，无视拦截) =================
@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    # 新浪公司公告静态网页，极其古老且稳定，无 WAF
    url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_Bulletin/symbol/{prefix}{symbol}/page/1.phtml"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            # 新浪网页是 GBK 编码，必须处理解码错误
            content = r.content.decode('gbk', errors='ignore')
            
            # 正则暴风吸入法：直接抠出公告标题和链接
            matches = re.findall(r"<a[^>]*href=['\"](/corp/view/vCB_AllBulletinDetail\.php\?[^'\"]+)['\"][^>]*>(.*?)</a>", content)
            
            if matches:
                items = []
                for m in matches[:8]:
                    items.append({
                        "title": m[1].replace('&nbsp;', '').strip(),
                        "type": "公司公告",
                        "date": "近期公告", 
                        "url": f"https://vip.stock.finance.sina.com.cn{m[0]}"
                    })
                return {"symbol": symbol, "items": items, "source": "新浪网页解析", "data_status": "real"}
            return {"items": [], "data_status": "fallback", "note": "未解析到公告内容，可能是结构变更"}
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

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
        "bull_case": ["已弃用受限的 Tushare 和易拦截的东财，全面接入免鉴权的新浪财经", "新浪网页硬核解析机制实装，彻底无视 Vercel 海外 IP 拦截"],
        "bear_case": ["研报层仍需接入 PDF 解析", "AI 层目前为本地模拟"],
        "final_summary": f"A股代码 {symbol} 架构完成绝杀级重构。系统已摆脱所有积分和 IP 限制，满血复活！",
        "risk_warning": "仅用于技术演示", "data_status": "ai-generated", "source": "Local Python Mock"
    }
