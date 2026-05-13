from fastapi import APIRouter, Query
from app.services.research_service import get_reports, get_consensus

router = APIRouter()

@router.get("/reports")
def reports(symbol: str = Query(...), limit: int = Query(10, ge=1, le=50)):
    return get_reports(symbol, limit=limit)

@router.get("/consensus")
def consensus(symbol: str = Query(...)):
    return get_consensus(symbol)
