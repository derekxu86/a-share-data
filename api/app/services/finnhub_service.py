from __future__ import annotations

import httpx
from app.config import settings

FINNHUB_BASE = "https://finnhub.io/api/v1"

async def finnhub_get(path: str, params: dict | None = None):
    """
    Finnhub helper.
    Requires FINNHUB_API_KEY in backend/.env.
    Useful for global market news and US stock reference data.
    """
    if not settings.finnhub_api_key:
        return None
    params = dict(params or {})
    params["token"] = settings.finnhub_api_key

    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(f"{FINNHUB_BASE}/{path}", params=params)
        if response.status_code >= 400:
            return {
                "error": response.text,
                "status_code": response.status_code,
                "source": f"finnhub.{path}"
            }
        return response.json()

async def get_market_news(category: str = "general", limit: int = 10):
    data = await finnhub_get("news", {"category": category})
    if data is None:
        return {
            "items": [],
            "source": "finnhub.news",
            "note": "FINNHUB_API_KEY not configured."
        }
    if isinstance(data, dict) and data.get("error"):
        return {"items": [], **data}
    return {
        "items": data[:limit] if isinstance(data, list) else [],
        "source": "finnhub.news"
    }

async def get_company_news(symbol: str, start: str, end: str, limit: int = 10):
    data = await finnhub_get("company-news", {"symbol": symbol, "from": start, "to": end})
    if data is None:
        return {
            "symbol": symbol,
            "items": [],
            "source": "finnhub.company-news",
            "note": "FINNHUB_API_KEY not configured."
        }
    if isinstance(data, dict) and data.get("error"):
        return {"symbol": symbol, "items": [], **data}
    return {
        "symbol": symbol,
        "items": data[:limit] if isinstance(data, list) else [],
        "source": "finnhub.company-news"
    }
