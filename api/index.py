import os
import sys
from pathlib import Path

# Make api/app importable on Vercel and local server.
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import market, research, signals, news, announcements, ai

app = FastAPI(
    title="AI Conviction Engine API",
    version="0.1.0",
    description="A股投研数据层 + AI Conviction 决策引擎"
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market.router, prefix="/api/market", tags=["行情层"])
app.include_router(research.router, prefix="/api/research", tags=["研报层"])
app.include_router(signals.router, prefix="/api/signals", tags=["信号层"])
app.include_router(news.router, prefix="/api/news", tags=["新闻层"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["公告层"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI总结层"])

@app.get("/api/health")
def health():
    return {
        "name": "AI Conviction Engine",
        "status": "ok",
        "runtime": "vercel-python"
    }

@app.get("/")
def root():
    return {
        "name": "AI Conviction Engine API",
        "status": "ok",
        "docs": "/docs",
        "health": "/api/health"
    }
