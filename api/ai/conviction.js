import { send } from '../_utils.js';

function fallback(payload) {
  return {
    conviction_score: 65,
    view: 'Neutral / Watchlist',
    market_regime: 'Unknown',
    factor_scores: {
      macro_tailwind: 60,
      momentum: 60,
      money_flow: 60,
      news_sentiment: 60,
      fundamental_quality: 60,
      valuation_risk: 50
    },
    bull_case: [
      '行情、资金、新闻、公告等数据层已接入框架。',
      '可作为观察池候选，但需要更多真实数据验证。'
    ],
    bear_case: [
      '部分数据层仍是占位接口，当前不能形成高置信度结论。',
      '需要结合估值、资金持续性、公告风险进一步验证。'
    ],
    final_summary: '当前给出中性观察观点。配置 OPENAI_API_KEY 后可启用真实 AI 决策分析。',
    risk_warning: '仅用于研究和教育演示，不构成投资建议。'
  };
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return send(res, 405, { error: 'Method not allowed' });

  let payload = {};
  try {
    payload = typeof req.body === 'object' ? req.body : JSON.parse(req.body || '{}');
  } catch {
    payload = {};
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return send(res, 200, fallback(payload));

  try {
    const model = process.env.OPENAI_MODEL || 'gpt-4o-mini';
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        temperature: 0.2,
        response_format: { type: 'json_object' },
        messages: [
          {
            role: 'system',
            content: '你是一个A股AI投研决策引擎。你不是荐股机器人，不给确定性买卖建议。你基于结构化数据输出可解释的 Conviction 分析。必须输出JSON。'
          },
          {
            role: 'user',
            content: `请基于以下结构化数据进行投研判断：\n${JSON.stringify(payload).slice(0, 12000)}\n\n输出JSON字段：conviction_score, view, market_regime, factor_scores, bull_case, bear_case, final_summary, risk_warning。`
          }
        ]
      })
    });

    const data = await response.json();
    const text = data.choices?.[0]?.message?.content;
    if (!response.ok || !text) {
      return send(res, 200, { ...fallback(payload), openai_error: data.error?.message || 'OpenAI request failed' });
    }

    try {
      return send(res, 200, JSON.parse(text));
    } catch {
      return send(res, 200, { ...fallback(payload), raw_text: text });
    }
  } catch (error) {
    return send(res, 200, { ...fallback(payload), error: String(error.message || error) });
  }
}
