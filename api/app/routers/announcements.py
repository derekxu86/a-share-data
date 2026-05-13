from fastapi import APIRouter, Query
from app.services.announcement_service import get_stock_announcements

router = APIRouter()

@router.get("/stock")
def stock_announcements(symbol: str = Query(...), limit: int = Query(20, ge=1, le=100)):
    return get_stock_announcements(symbol, limit=limit)
