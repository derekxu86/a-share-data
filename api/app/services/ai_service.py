import json
from app.config import settings

def build_fallback_conviction(payload: dict):
    return {
        "conviction_score": 65,
        "view": "Neutral / Watchlist",
        "market_regime": "Unknown",
        "factor_scores": {
            "macro_tailwind": 60,
            "momentum": 60,
            "money_flow": 60,
            "news_sentiment": 60,
            "fundamental_quality": 60,
            "valuation_risk": 50
        },
        "bull_case": [
            "已有行情、资金、新闻、公告等数据输入，可进入观察池。",
            "后续可接入更多实时信号提升判断可靠性。"
        ],
        "bear_case": [
            "当前数据不足，不能形成高置信度结论。",
            "需要结合估值、资金持续性和公告风险进一步验证。"
        ],
        "final_summary": "当前仅给出中性观察观点。请配置 OPENAI_API_KEY 以启用真实 AI 决策分析。",
        "risk_warning": "仅用于研究和教育演示，不构成投资建议。"
    }

async def generate_conviction(payload: dict):
    if not settings.openai_api_key:
        return build_fallback_conviction(payload)

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    system = """
你是一个A股AI投研决策引擎。你不是荐股机器人，不给确定性买卖建议。
你需要基于结构化数据输出可解释的 Conviction 分析。
必须包含 bull case、bear case、factor scores、market regime、final view。
输出必须是 JSON。
"""

    user = f"""
请基于以下结构化数据进行投研判断：
{json.dumps(payload, ensure_ascii=False)[:12000]}

输出 JSON 字段：
conviction_score: 0-100
view: Bearish / Neutral / Watchlist / Moderately Bullish / High Conviction
market_regime: 当前市场状态
factor_scores: macro_tailwind, momentum, money_flow, news_sentiment, fundamental_quality, valuation_risk
bull_case: string[]
bear_case: string[]
final_summary: string
risk_warning: string
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    text = response.choices[0].message.content
    try:
        return json.loads(text)
    except Exception:
        result = build_fallback_conviction(payload)
        result["raw_text"] = text
        return result
