from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import re
import json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://finance.sina.com.cn/'
}

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
                    "status": "real"
                }
    return None

async def fetch_sina_quote(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://hq.sinajs.cn/list={prefix}{symbol}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code == 200 and '=' in r.text:
            data = re.search(r'="(.*)"', r.text).group(1).split(',')
            if len(data) > 3:
                price = float(data[3])
                prev_close = float(data[2])
                change = ((price - prev_close) / prev_close) * 100 if prev_close else 0
                return {
                    "symbol": symbol,
                    "name": data[0],
                    "price": price,
                    "change_pct": round(change, 2),
                    "source": "新浪财经",
                    "status": "real"
                }
    return None

@app.get("/api/market/quote")
async def get_quote(symbol: str):
    # 链式回退：腾讯 -> 新浪 -> 错误
    res = await fetch_tencent_quote(symbol)
    if res: return res
    
    res = await fetch_sina_quote(symbol)
    if res: return res
    
    raise HTTPException(status_code=404, detail="行情源全部失效")

@app.get("/api/news/stock")
async def get_news(symbol: str):
    prefix = 'sh' if symbol.startswith('6') else 'sz'
    url = f"https://finance.pae.baidu.com/vapi/v1/getnewsinfo?code={prefix}{symbol}&rn=8"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        data = r.json()
        items = data.get('Result', {}).get('list', [])
        return {
            "items": [{"title": i['title'], "source": i['source'], "date": i['time'], "url": i['url']} for i in items],
            "source": "百度股市通",
            "status": "real"
        }

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
                items.append({
                    "symbol": p[1],
                    "name": p[2],
                    "py": p[3],
                    "market": p[0].upper()
                })
        return {"items": items[:10]}

@app.get("/api/health")
def health():
    return {"status": "ok", "backend": "FastAPI"}
