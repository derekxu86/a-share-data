import math
import pandas as pd

def safe_float(value, default=None):
    try:
        if value is None:
            return default
        if isinstance(value, float) and math.isnan(value):
            return default
        return float(value)
    except Exception:
        return default

def safe_str(value, default=""):
    if value is None:
        return default
    return str(value)

def df_to_records(df: pd.DataFrame, limit: int = 30):
    if df is None or df.empty:
        return []
    clean = df.head(limit).replace({float("nan"): None})
    return clean.to_dict(orient="records")
