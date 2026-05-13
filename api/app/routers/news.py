from fastapi import APIRouter, Query
from app.services.news_service import get_latest_news, get_stock_news, get_global_market_news

router = APIRouter()

@router.get("/latest")
def latest(limit: int = Query(20, ge=1, le=100)):
    return get_latest_news(limit=limit)

@router.get("/stock")
def stock_news(symbol: str = Query(...), limit: int = Query(20, ge=1, le=100)):
    return get_stock_news(symbol, limit=limit)


@router.get("/global")
async def global_market_news(limit: int = Query(10, ge=1, le=50)):
    return await get_global_market_news(limit=limit)
