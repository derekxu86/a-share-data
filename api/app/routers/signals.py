from fastapi import APIRouter, Query
from app.services.signal_service import (
    get_signal_overview,
    get_money_flow,
    get_northbound,
    get_dragon_tiger,
    get_sector_ranking,
)

router = APIRouter()

@router.get("/overview")
def overview(symbol: str = Query(...)):
    return get_signal_overview(symbol)

@router.get("/money-flow")
def money_flow(symbol: str = Query(...)):
    return get_money_flow(symbol)

@router.get("/northbound")
def northbound():
    return get_northbound()

@router.get("/dragon-tiger")
def dragon_tiger(limit: int = Query(20, ge=1, le=100)):
    return get_dragon_tiger(limit=limit)

@router.get("/sector-ranking")
def sector_ranking(limit: int = Query(30, ge=1, le=100)):
    return get_sector_ranking(limit=limit)
