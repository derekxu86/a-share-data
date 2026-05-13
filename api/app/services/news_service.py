from app.utils.format import df_to_records
from app.services.market_service import normalize_symbol

def get_latest_news(limit: int = 20):
    try:
        import akshare as ak
        if hasattr(ak, "stock_news_em"):
            df = ak.stock_news_em(symbol="300059")
            return {"items": df_to_records(df, limit), "source": "akshare.stock_news_em"}
    except Exception as exc:
        return {"items": [], "source": "mock", "error": str(exc)}
    return {"items": [], "source": "placeholder"}

def get_stock_news(symbol: str, limit: int = 20):
    code = normalize_symbol(symbol)
    try:
        import akshare as ak
        if hasattr(ak, "stock_news_em"):
            df = ak.stock_news_em(symbol=code)
            return {"symbol": code, "items": df_to_records(df, limit), "source": "akshare.stock_news_em"}
    except Exception as exc:
        return {"symbol": code, "items": [], "source": "mock", "error": str(exc)}
    return {"symbol": code, "items": [], "source": "placeholder"}


async def get_global_market_news(limit: int = 10):
    try:
        from app.services.finnhub_service import get_market_news
        return await get_market_news(category="general", limit=limit)
    except Exception as exc:
        return {"items": [], "source": "mock", "error": str(exc)}
