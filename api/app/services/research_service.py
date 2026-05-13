from app.utils.format import df_to_records
from app.services.market_service import normalize_symbol

def get_reports(symbol: str, limit: int = 10):
    """
    东方财富研报数据在 AkShare 不同版本中函数名可能变化。
    这里采用防御式写法：可跑则返回真实数据，不可跑则返回空结果。
    """
    code = normalize_symbol(symbol)
    try:
        import akshare as ak
        # 常见函数：stock_research_report_em / stock_research_report_summary_em
        if hasattr(ak, "stock_research_report_em"):
            df = ak.stock_research_report_em(symbol=code)
        elif hasattr(ak, "stock_research_report_summary_em"):
            df = ak.stock_research_report_summary_em(symbol=code)
        else:
            return {"symbol": code, "reports": [], "source": "akshare", "note": "当前 AkShare 版本未找到研报函数"}
        return {"symbol": code, "reports": df_to_records(df, limit), "source": "akshare.eastmoney_research"}
    except Exception as exc:
        return {"symbol": code, "reports": [], "source": "mock", "error": str(exc)}

def get_consensus(symbol: str):
    return {
        "symbol": normalize_symbol(symbol),
        "eps": [],
        "rating": None,
        "source": "placeholder",
        "note": "可后续接东方财富一致预期或 Tushare Pro。"
    }
