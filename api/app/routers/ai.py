from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
from app.services.ai_service import generate_conviction

router = APIRouter()

class ConvictionRequest(BaseModel):
    symbol: str
    market: dict[str, Any] | None = None
    research: dict[str, Any] | None = None
    signals: dict[str, Any] | None = None
    news: dict[str, Any] | None = None
    announcements: dict[str, Any] | None = None

@router.post("/conviction")
async def conviction(req: ConvictionRequest):
    return await generate_conviction(req.model_dump())
