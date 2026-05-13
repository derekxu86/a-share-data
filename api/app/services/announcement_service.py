from app.utils.format import df_to_records
from app.services.market_service import normalize_symbol

def get_stock_announcements(symbol: str, limit: int = 20):
    code = normalize_symbol(symbol)
    try:
        import akshare as ak
        # 巨潮公告相关函数在不同版本可能不同，所以防御处理
        candidates = [
            "stock_notice_report",
            "stock_zh_a_disclosure_report_cninfo",
        ]
        for name in candidates:
            if hasattr(ak, name):
                func = getattr(ak, name)
                try:
                    df = func(symbol=code)
                except TypeError:
                    df = func()
                return {"symbol": code, "items": df_to_records(df, limit), "source": f"akshare.{name}"}
    except Exception as exc:
        return {"symbol": code, "items": [], "source": "mock", "error": str(exc)}
    return {"symbol": code, "items": [], "source": "placeholder", "note": "可后续接巨潮资讯 CNInfo 接口。"}
