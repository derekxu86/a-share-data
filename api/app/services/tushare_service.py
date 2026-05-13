from __future__ import annotations

from functools import lru_cache
from app.config import settings
from app.services.market_service import normalize_symbol
from app.utils.format import safe_float, df_to_records

@lru_cache(maxsize=1)
def get_tushare_pro():
    """
    Tushare Pro client.
    Requires TUSHARE_TOKEN in backend/.env.
    """
    if not settings.tushare_token:
        return None
    try:
        import tushare as ts
        ts.set_token(settings.tushare_token)
        return ts.pro_api()
    except Exception:
        return None

def to_ts_code(symbol: str) -> str:
    code = normalize_symbol(symbol)
    if code.startswith("6"):
        return f"{code}.SH"
    return f"{code}.SZ"

def get_daily_basic(symbol: str):
    """
    Tushare daily_basic:
    PE/PB/turnover/market cap data.
    Usually requires basic Tushare permissions/points.
    """
    pro = get_tushare_pro()
    if not pro:
        return None

    ts_code = to_ts_code(symbol)
    try:
        df = pro.daily_basic(
            ts_code=ts_code,
            fields="ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,total_mv,circ_mv"
        )
        if df is None or df.empty:
            return None
        r = df.iloc[0]
        return {
            "ts_code": str(r.get("ts_code")),
            "trade_date": str(r.get("trade_date")),
            "close": safe_float(r.get("close")),
            "turnover_rate": safe_float(r.get("turnover_rate")),
            "volume_ratio": safe_float(r.get("volume_ratio")),
            "pe": safe_float(r.get("pe")),
            "pb": safe_float(r.get("pb")),
            "total_mv": safe_float(r.get("total_mv")),
            "circ_mv": safe_float(r.get("circ_mv")),
            "source": "tushare.daily_basic"
        }
    except Exception as exc:
        return {"error": str(exc), "source": "tushare.daily_basic"}

def get_stock_company(symbol: str):
    """
    Basic company information from Tushare.
    """
    pro = get_tushare_pro()
    if not pro:
        return None

    ts_code = to_ts_code(symbol)
    try:
        df = pro.stock_company(ts_code=ts_code)
        if df is None or df.empty:
            return None
        return {
            "items": df_to_records(df, 3),
            "source": "tushare.stock_company"
        }
    except Exception as exc:
        return {"items": [], "error": str(exc), "source": "tushare.stock_company"}

def get_moneyflow(symbol: str):
    """
    Tushare moneyflow endpoint.
    Useful for main/retail/small/large money flow analysis.
    Permission depends on Tushare account level.
    """
    pro = get_tushare_pro()
    if not pro:
        return None

    ts_code = to_ts_code(symbol)
    try:
        df = pro.moneyflow(ts_code=ts_code)
        return {
            "items": df_to_records(df, 20),
            "source": "tushare.moneyflow"
        }
    except Exception as exc:
        return {"items": [], "error": str(exc), "source": "tushare.moneyflow"}
