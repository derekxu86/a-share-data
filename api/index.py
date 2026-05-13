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
    return httpx.AsyncClient(follow_redirects=True, verify=False, timeout=15.0)

# ================= 1. 行情层 =================
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

# ================= 3. 新闻层 =================
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

# ================= 4. 公告层 (引入 re.DOTALL 跨行修复版) =================
@app.get("/api/announcements/stock")
async def get_announcements(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_Bulletin/symbol/{prefix}{symbol}/page/1.phtml"
    async with get_client() as client:
        try:
            r = await client.get(url, headers=HEADERS)
            content = r.content.decode('gbk', errors='ignore')
            
            # 关键修复：加入 re.DOTALL 允许跨行匹配。解决新浪在标题中间强行回车导致正则断裂的问题
            matches = re.findall(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', content, re.IGNORECASE | re.DOTALL)
            
            if matches:
                items = []
                seen_urls = set()
                for m in matches:
                    if len(items) >= 8: break
                    url_match = m[0].strip()
                    
                    # 清洗标题：去掉 HTML 标签，并把所有换行符和制表符彻底抹除
                    title = re.sub(r'<[^>]+>', '', m[1])
                    title = title.replace('&nbsp;', '').replace('\n', '').replace('\r', '').replace('\t', '').strip()
                    
                    # 核心过滤：必须包含 bulletin 且有 id= 参数
                    if 'bulletin' in url_match.lower() and 'id=' in url_match.lower():
                        if not title or len(title) <= 4 or '更多' in title: 
                            continue
                            
                        if not url_match.startswith('http'):
                            url_match = f"https://vip.stock.finance.sina.com.cn{url_match}"
                            
                        if url_match in seen_urls: continue
                        seen_urls.add(url_match)
                        
                        items.append({
                            "title": title,
                            "type": "公司公告",
                            "date": "最新披露", 
                            "url": url_match,
                            "summary": title
                        })
                        
                if items:
                    return {"symbol": symbol, "items": items, "source": "新浪网页精准解析", "data_status": "real"}
            
            return {"items": [], "data_status": "fallback", "note": "未能精准匹配到真实公告内容"}
            
        except Exception as e:
            return {"items": [], "data_status": "fallback", "note": f"抓取异常: {str(e)}"}

# ================= 5 & 6. 研报与信号层 (预留占位) =================
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
        "factor_scores": {"quote_layer": random.randint(40, 90), "research_layer": 50, "signal_layer
