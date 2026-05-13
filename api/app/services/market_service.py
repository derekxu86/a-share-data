from __future__ import annotations

from app.utils.format import safe_float
import pandas as pd

def normalize_symbol(symbol: str) -> str:
    return str(symbol).strip().upper().replace(".SH", "").replace(".SZ", "")

def _mock_quote(symbol: str):
    return {
        "symbol": symbol,
        "name": "示例股票",
        "price": 0,
        "change_pct": 0,
        "pe": None,
        "pb": None,
        "market_cap": None,
        "turnover_rate": None,
        "source": "mock",
        "note": "真实数据源不可用时返回占位数据。请确认 akshare/mootdx 是否安装并可访问。"
    }

def get_quote(symbol: str):
    """
    第一版优先用 AkShare 做稳妥 fallback。
    后续可接 mootdx 实时盘口。
    """
    code = normalize_symbol(symbol)
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"].astype(str) == code]
        if row.empty:
            return _mock_quote(code)
        r = row.iloc[0]
        result = {
            "symbol": code,
            "name": str(r.get("名称", "")),
            "price": safe_float(r.get("最新价"), 0),
            "change_pct": safe_float(r.get("涨跌幅"), 0),
            "pe": safe_float(r.get("市盈率-动态")),
            "pb": safe_float(r.get("市净率")),
            "market_cap": safe_float(r.get("总市值")),
            "turnover_rate": safe_float(r.get("换手率")),
            "volume": safe_float(r.get("成交量")),
            "amount": safe_float(r.get("成交额")),
            "source": "akshare.stock_zh_a_spot_em"
        }

        # Optional enrichment from Tushare Pro if TUSHARE_TOKEN is configured.
        try:
            from app.services.tushare_service import get_daily_basic
            tushare_basic = get_daily_basic(code)
            if tushare_basic and not tushare_basic.get("error"):
                result["tushare_basic"] = tushare_basic
                result["pe"] = tushare_basic.get("pe") or result.get("pe")
                result["pb"] = tushare_basic.get("pb") or result.get("pb")
                result["turnover_rate"] = tushare_basic.get("turnover_rate") or result.get("turnover_rate")
                result["market_cap"] = tushare_basic.get("total_mv") or result.get("market_cap")
        except Exception:
            pass

        return result
    except Exception as exc:
        data = _mock_quote(code)
        data["error"] = str(exc)
        return data

def get_kline(symbol: str, period: str = "daily", adjust: str = "qfq", limit: int = 120):
    code = normalize_symbol(symbol)
    period_map = {
        "daily": "daily",
        "weekly": "weekly",
        "monthly": "monthly",
        "minute": "1"
    }
    try:
        import akshare as ak
        ak_period = period_map.get(period, "daily")
        df = ak.stock_zh_a_hist(symbol=code, period=ak_period, adjust=adjust)
        if df is None or df.empty:
            return {"symbol": code, "items": [], "source": "akshare.stock_zh_a_hist"}
        df = df.tail(limit)
        items = []
        for _, r in df.iterrows():
            items.append({
                "date": str(r.get("日期")),
                "open": safe_float(r.get("开盘")),
                "high": safe_float(r.get("最高")),
                "low": safe_float(r.get("最低")),
                "close": safe_float(r.get("收盘")),
                "volume": safe_float(r.get("成交量")),
                "amount": safe_float(r.get("成交额")),
                "change_pct": safe_float(r.get("涨跌幅"))
            })
        return {"symbol": code, "items": items, "source": "akshare.stock_zh_a_hist"}
    except Exception as exc:
        return {"symbol": code, "items": [], "source": "mock", "error": str(exc)}
