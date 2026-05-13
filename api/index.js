function send(res, status, payload) {
  res.status(status).setHeader('content-type', 'application/json; charset=utf-8');
  res.setHeader('cache-control', 's-maxage=60, stale-while-revalidate=300');
  res.json(payload);
}

function getSymbol(req) {
  return String(req.query.symbol || '').trim().toUpperCase().replace('.SH', '').replace('.SZ', '');
}

function toSecid(symbol) {
  const code = String(symbol || '').replace('.SH', '').replace('.SZ', '');
  if (code.startsWith('6')) return `1.${code}`;
  return `0.${code}`;
}

function toTsCode(symbol) {
  const code = String(symbol || '').replace('.SH', '').replace('.SZ', '');
  if (code.startsWith('6')) return `${code}.SH`;
  return `${code}.SZ`;
}

async function tushare(apiName, params = {}, fields = '') {
  const token = process.env.TUSHARE_TOKEN;
  if (!token) {
    return { ok: false, error: 'TUSHARE_TOKEN not configured', items: [] };
  }

  const response = await fetch('https://api.tushare.pro', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      api_name: apiName,
      token,
      params,
      fields
    })
  });

  const data = await response.json();
  if (!response.ok || data.code !== 0) {
    return { ok: false, error: data.msg || 'Tushare request failed', raw: data, items: [] };
  }

  const columns = data.data?.fields || [];
  const rows = data.data?.items || [];
  const items = rows.map(row => Object.fromEntries(columns.map((c, i) => [c, row[i]])));
  return { ok: true, items, source: `tushare.${apiName}` };
}

function fallbackConviction(payload) {
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

async function handleHealth(req, res) {
  return send(res, 200, {
    name: 'AI Conviction Engine',
    status: 'ok',
    runtime: 'vercel-node',
    api: 'single-function'
  });
}

async function handleMarketQuote(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    const fields = [
      'f43','f44','f45','f46','f47','f48','f57','f58','f60',
      'f116','f117','f162','f167','f168','f169','f170'
    ].join(',');

    const url = `https://push2.eastmoney.com/api/qt/stock/get?secid=${toSecid(symbol)}&fields=${fields}`;
    const r = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' } });
    const data = await r.json();
    const d = data?.data || {};

    function scalePrice(v) {
      const n = Number(v);
      if (!Number.isFinite(n)) return null;
      return n / 100;
    }

    function scalePct(v) {
      const n = Number(v);
      if (!Number.isFinite(n)) return null;
      return n / 100;
    }

    let result = {
      symbol,
      ts_code: toTsCode(symbol),
      name: d.f58 || symbol,
      price: scalePrice(d.f43),
      open: scalePrice(d.f46),
      high: scalePrice(d.f44),
      low: scalePrice(d.f45),
      previous_close: scalePrice(d.f60),
      change: scalePrice(d.f169),
      change_pct: scalePct(d.f170),
      volume: Number(d.f47 || 0),
      amount: Number(d.f48 || 0),
      pe: Number.isFinite(Number(d.f162)) ? Number(d.f162) : null,
      pb: Number.isFinite(Number(d.f167)) ? Number(d.f167) : null,
      turnover_rate: scalePct(d.f168),
      market_cap: Number.isFinite(Number(d.f116)) ? Number(d.f116) : null,
      float_market_cap: Number.isFinite(Number(d.f117)) ? Number(d.f117) : null,
      source: 'eastmoney.push2'
    };

    const ts = await tushare(
      'daily_basic',
      { ts_code: toTsCode(symbol), limit: 1 },
      'ts_code,trade_date,close,turnover_rate,volume_ratio,pe,pb,total_mv,circ_mv'
    );

    if (ts.ok && ts.items?.[0]) {
      result.tushare_basic = ts.items[0];
      result.pe = ts.items[0].pe ?? result.pe;
      result.pb = ts.items[0].pb ?? result.pb;
      result.turnover_rate = ts.items[0].turnover_rate ?? result.turnover_rate;
      result.market_cap = ts.items[0].total_mv ?? result.market_cap;
    }

    return send(res, 200, result);
  } catch (error) {
    return send(res, 200, {
      symbol,
      name: symbol,
      price: null,
      change_pct: null,
      source: 'safe-fallback',
      error: String(error.message || error)
    });
  }
}

async function handleMarketKline(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    const data = await tushare(
      'daily',
      { ts_code: toTsCode(symbol), limit: Number(req.query.limit || 120) },
      'ts_code,trade_date,open,high,low,close,vol,amount'
    );

    if (!data.ok) return send(res, 200, { symbol, items: [], source: 'tushare.daily', error: data.error });

    return send(res, 200, {
      symbol,
      items: data.items.reverse(),
      source: 'tushare.daily'
    });
  } catch (error) {
    return send(res, 200, { symbol, items: [], source: 'safe-fallback', error: String(error.message || error) });
  }
}

async function handleResearchReports(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    const forecast = await tushare(
      'forecast',
      { ts_code: toTsCode(symbol), limit: 10 },
      'ts_code,ann_date,end_date,type,p_change_min,p_change_max,net_profit_min,net_profit_max,summary'
    );

    const forecasts = forecast.ok ? forecast.items : [];
    return send(res, 200, {
      symbol,
      reports: [],
      forecasts,
      source: forecast.ok ? 'tushare.forecast' : 'placeholder',
      note: forecasts.length > 0
        ? 'Tushare forecast data returned.'
        : (forecast.error || '当前接口未返回研报/EPS预测。下一步可接东方财富研报PDF或巨潮公告。'),
      status: forecasts.length > 0 ? 'ok' : 'empty'
    });
  } catch (error) {
    return send(res, 200, { symbol, reports: [], forecasts: [], source: 'safe-fallback', error: String(error.message || error) });
  }
}

async function handleSignalsOverview(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    const moneyflow = await tushare(
      'moneyflow',
      { ts_code: toTsCode(symbol), limit: 20 },
      'ts_code,trade_date,buy_sm_vol,buy_sm_amount,sell_sm_vol,sell_sm_amount,buy_lg_vol,buy_lg_amount,sell_lg_vol,sell_lg_amount,buy_elg_vol,buy_elg_amount,sell_elg_vol,sell_elg_amount,net_mf_vol,net_mf_amount'
    );

    return send(res, 200, {
      symbol,
      money_flow: {
        items: moneyflow.ok ? moneyflow.items : [],
        source: moneyflow.ok ? 'tushare.moneyflow' : 'placeholder',
        error: moneyflow.ok ? null : moneyflow.error
      },
      northbound: { items: [], source: 'placeholder', note: 'Can add hk_hold / hsgt endpoints later.' },
      dragon_tiger: { items: [], source: 'placeholder', note: 'Can add Eastmoney/Tushare 龙虎榜 later.' },
      sector_ranking: { items: [], source: 'placeholder', note: 'Can add Eastmoney board ranking later.' }
    });
  } catch (error) {
    return send(res, 200, { symbol, source: 'safe-fallback', error: String(error.message || error) });
  }
}

async function handleGlobalNews(req, res) {
  const token = process.env.FINNHUB_API_KEY;
  if (!token) return send(res, 200, { items: [], source: 'finnhub.news', note: 'FINNHUB_API_KEY not configured' });

  try {
    const limit = Number(req.query.limit || 10);
    const r = await fetch(`https://finnhub.io/api/v1/news?category=general&token=${token}`);
    const data = await r.json();
    return send(res, 200, {
      items: Array.isArray(data) ? data.slice(0, limit) : [],
      source: 'finnhub.news'
    });
  } catch (error) {
    return send(res, 200, { items: [], source: 'safe-fallback', error: String(error.message || error) });
  }
}

async function handleStockNews(req, res) {
  const symbol = getSymbol(req);
  return send(res, 200, {
    symbol,
    items: [],
    source: 'placeholder',
    note: 'A-share stock news layer reserved. Use global news first, or add Eastmoney/Cailianshe endpoint later.'
  });
}

async function handleAnnouncements(req, res) {
  const symbol = getSymbol(req);
  return send(res, 200, {
    symbol,
    items: [],
    source: 'placeholder',
    note: 'Announcement layer reserved for CNInfo/Eastmoney announcements.'
  });
}

async function handleAiConviction(req, res) {
  if (req.method !== 'POST') return send(res, 405, { error: 'Method not allowed' });

  let payload = {};
  try {
    payload = typeof req.body === 'object' ? req.body : JSON.parse(req.body || '{}');
  } catch {
    payload = {};
  }

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return send(res, 200, fallbackConviction(payload));

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
      return send(res, 200, { ...fallbackConviction(payload), openai_error: data.error?.message || 'OpenAI request failed' });
    }

    try {
      return send(res, 200, JSON.parse(text));
    } catch {
      return send(res, 200, { ...fallbackConviction(payload), raw_text: text });
    }
  } catch (error) {
    return send(res, 200, { ...fallbackConviction(payload), error: String(error.message || error) });
  }
}

async function handlePlaceholder(req, res, source) {
  return send(res, 200, {
    items: [],
    source: 'placeholder',
    note: `${source} endpoint is reserved.`
  });
}

export default async function handler(req, res) {
  const path = req.url.split('?')[0].replace(/\/+$/, '') || '/api';

  try {
    if (path === '/api' || path === '/api/health') return handleHealth(req, res);

    if (path === '/api/market/quote') return handleMarketQuote(req, res);
    if (path === '/api/market/kline') return handleMarketKline(req, res);

    if (path === '/api/research/reports') return handleResearchReports(req, res);

    if (path === '/api/signals/overview') return handleSignalsOverview(req, res);
    if (path === '/api/signals/money-flow') return handlePlaceholder(req, res, 'money-flow');
    if (path === '/api/signals/northbound') return handlePlaceholder(req, res, 'northbound');
    if (path === '/api/signals/dragon-tiger') return handlePlaceholder(req, res, 'dragon-tiger');
    if (path === '/api/signals/sector-ranking') return handlePlaceholder(req, res, 'sector-ranking');

    if (path === '/api/news/global') return handleGlobalNews(req, res);
    if (path === '/api/news/stock') return handleStockNews(req, res);
    if (path === '/api/news/latest') return handlePlaceholder(req, res, 'latest-news');

    if (path === '/api/announcements/stock') return handleAnnouncements(req, res);

    if (path === '/api/ai/conviction') return handleAiConviction(req, res);

    return send(res, 404, {
      error: 'Endpoint not found',
      path,
      available: [
        '/api/health',
        '/api/market/quote?symbol=600519',
        '/api/market/kline?symbol=600519',
        '/api/research/reports?symbol=600519',
        '/api/signals/overview?symbol=600519',
        '/api/news/global',
        '/api/news/stock?symbol=600519',
        '/api/announcements/stock?symbol=600519',
        '/api/ai/conviction'
      ]
    });
  } catch (error) {
    return send(res, 200, {
      source: 'single-function-fallback',
      error: String(error.message || error)
    });
  }
}
