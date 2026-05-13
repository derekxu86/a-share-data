from fastapi import APIRouter, Query
from app.services.market_service import get_quote, get_kline

router = APIRouter()

@router.get("/quote")
def quote(symbol: str = Query(..., description="A股代码，例如 600519")):
    return get_quote(symbol)

@router.get("/kline")
def kline(
    symbol: str = Query(...),
    period: str = Query("daily", description="daily / weekly / monthly / minute"),
    limit: int = Query(120, ge=10, le=500)
):
    return get_kline(symbol, period=period, limit=limit)
