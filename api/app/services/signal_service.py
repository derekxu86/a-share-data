from app.utils.format import df_to_records
from app.services.market_service import normalize_symbol

def get_signal_overview(symbol: str):
    code = normalize_symbol(symbol)
    return {
        "symbol": code,
        "money_flow": get_money_flow(code),
        "northbound": get_northbound(),
        "dragon_tiger": get_dragon_tiger(limit=10),
        "sector_ranking": get_sector_ranking(limit=20)
    }

def get_money_flow(symbol: str):
    code = normalize_symbol(symbol)

    # Optional Tushare Pro moneyflow first, if TUSHARE_TOKEN is configured.
    try:
        from app.services.tushare_service import get_moneyflow
        tushare_flow = get_moneyflow(code)
        if tushare_flow and tushare_flow.get("items"):
            return {"symbol": code, **tushare_flow}
    except Exception:
        pass

    # Fallback to AkShare.
    try:
        import akshare as ak
        if hasattr(ak, "stock_individual_fund_flow"):
            df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith("6") else "sz")
            return {
                "symbol": code,
                "items": df_to_records(df, 20),
                "source": "akshare.stock_individual_fund_flow"
            }
    except Exception as exc:
        return {"symbol": code, "items": [], "source": "mock", "error": str(exc)}
    return {"symbol": code, "items": [], "source": "placeholder"}

def get_northbound():
    try:
        import akshare as ak
        if hasattr(ak, "stock_hsgt_north_net_flow_in_em"):
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
            return {"items": df_to_records(df, 20), "source": "akshare.hsgt"}
    except Exception as exc:
        return {"items": [], "source": "mock", "error": str(exc)}
    return {"items": [], "source": "placeholder"}

def get_dragon_tiger(limit: int = 20):
    try:
        import akshare as ak
        if hasattr(ak, "stock_lhb_detail_daily_sina"):
            df = ak.stock_lhb_detail_daily_sina()
            return {"items": df_to_records(df, limit), "source": "akshare.lhb"}
    except Exception as exc:
        return {"items": [], "source": "mock", "error": str(exc)}
    return {"items": [], "source": "placeholder"}

def get_sector_ranking(limit: int = 30):
    try:
        import akshare as ak
        if hasattr(ak, "stock_board_industry_name_em"):
            boards = ak.stock_board_industry_name_em()
            return {"items": df_to_records(boards, limit), "source": "akshare.stock_board_industry_name_em"}
    except Exception as exc:
        return {"items": [], "source": "mock", "error": str(exc)}
    return {"items": [], "source": "placeholder"}
