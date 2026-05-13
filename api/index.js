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

function toMarketSymbol(symbol) {
  const code = String(symbol || '').replace('.SH', '').replace('.SZ', '');
  if (code.startsWith('6')) return `sh${code}`;
  return `sz${code}`;
}

const STOCK_META = {
  '600519': { name: '贵州茅台', theme: '白酒消费', industry: '食品饮料', basePrice: 1534.5 },
  '002415': { name: '海康威视', theme: 'AI安防 / 机器视觉', industry: '计算机设备', basePrice: 28.6 },
  '300750': { name: '宁德时代', theme: '新能源电池', industry: '电力设备', basePrice: 186.2 },
  '002594': { name: '比亚迪', theme: '新能源汽车', industry: '汽车整车', basePrice: 214.8 },
  '300059': { name: '东方财富', theme: '互联网券商', industry: '非银金融', basePrice: 13.8 },
  '601012': { name: '隆基绿能', theme: '光伏', industry: '电力设备', basePrice: 15.2 },
  '688981': { name: '中芯国际', theme: '半导体制造', industry: '半导体', basePrice: 51.5 },
  '600036': { name: '招商银行', theme: '银行 / 高股息', industry: '银行', basePrice: 38.1 }
};

function getMeta(symbol) {
  return STOCK_META[symbol] || {
    name: symbol,
    theme: 'A股个股',
    industry: '未分类',
    basePrice: 10 + (Number(symbol.slice(-2)) || 1)
  };
}

function pseudo(symbol, min, max) {
  const n = String(symbol).split('').reduce((acc, x) => acc + Number(x || 0), 0);
  return Number((min + (n % 100) / 100 * (max - min)).toFixed(2));
}

function demoQuote(symbol, reason = '真实行情接口暂不可用，返回结构化演示数据。') {
  const meta = getMeta(symbol);
  return {
    symbol,
    name: meta.name,
    price: meta.basePrice,
    open: Number((meta.basePrice * 0.992).toFixed(2)),
    high: Number((meta.basePrice * 1.018).toFixed(2)),
    low: Number((meta.basePrice * 0.981).toFixed(2)),
    previous_close: Number((meta.basePrice * 0.996).toFixed(2)),
    change_pct: pseudo(symbol, -1.8, 2.4),
    pe: pseudo(symbol, 18, 42),
    pb: pseudo(symbol, 1.8, 8.5),
    turnover_rate: pseudo(symbol, 0.6, 4.8),
    market_cap: Math.round(meta.basePrice * 1000000000),
    source: 'structured-fallback',
    preferred_sources: ['mootdx', '腾讯财经', '东方财富'],
    note: reason
  };
}

function demoResearch(symbol, reason = '东方财富 PDF / 研报接口暂未返回数据。') {
  const meta = getMeta(symbol);
  return {
    symbol,
    reports: [
      {
        title: `${meta.name}：围绕${meta.theme}的中长期逻辑跟踪`,
        broker: '东方财富PDF层 / fallback',
        rating: '观察',
        summary: `重点关注${meta.industry}景气度、盈利修复和估值变化。`
      },
      {
        title: `${meta.industry}行业比较：资金轮动与估值位置`,
        broker: '研报层 / fallback',
        rating: '中性',
        summary: `该层用于承接东方财富研报PDF、机构评级、EPS预测和一致预期。`
      }
    ],
    forecasts: [
      {
        type: 'EPS趋势占位',
        end_date: '未来12个月',
        summary: `后续可接东方财富研报PDF解析、机构EPS一致预期。`
      }
    ],
    source: '东方财富PDF / structured-fallback',
    status: 'fallback',
    note: reason
  };
}

function demoSignals(symbol, reason = '同花顺 / 百度股市通 / 东方财富资金流暂未返回数据。') {
  const meta = getMeta(symbol);
  const main = pseudo(symbol, -1.2, 2.8);
  return {
    symbol,
    money_flow: {
      items: [
        { label: '主力净流入估算', value: `${main} 亿`, signal: main > 0 ? 'positive' : 'neutral' },
        { label: '超大单方向', value: main > 1 ? '偏流入' : '分歧', signal: main > 1 ? 'positive' : 'mixed' },
        { label: '20日资金趋势', value: pseudo(symbol, 40, 78), signal: 'watch' }
      ],
      source: '同花顺 / 东方财富资金流 fallback',
      error: null
    },
    northbound: {
      items: [{ label: '北向资金', value: '待接入东方财富/同花顺北向资金', signal: 'pending' }],
      source: '东方财富 / 同花顺 placeholder'
    },
    dragon_tiger: {
      items: [{ label: '龙虎榜', value: '待接入东方财富/同花顺龙虎榜', signal: 'pending' }],
      source: '东方财富 / 同花顺 placeholder'
    },
    sector_ranking: {
      items: [{ label: meta.industry, value: `${meta.theme}`, signal: 'theme-map' }],
      source: '百度股市通 / 同花顺 structured-fallback'
    },
    note: reason
  };
}

function demoNews(symbol, reason = '百度股市通 / 财经新闻接口暂未返回数据。') {
  const meta = getMeta(symbol);
  return {
    symbol,
    items: [
      {
        title: `${meta.industry}板块进入AI新闻监控池`,
        source: '百度股市通 / 腾讯财经 fallback',
        sentiment: 'neutral',
        summary: `跟踪${meta.name}相关政策、订单、业绩和行业景气度变化。`
      },
      {
        title: `${meta.theme}主题热度待实时新闻源验证`,
        source: '新闻层 fallback',
        sentiment: 'watch',
        summary: '后续可接百度股市通、腾讯财经、财联社或东方财富新闻。'
      }
    ],
    source: '百度股市通 / 腾讯财经 structured-fallback',
    note: reason
  };
}

function demoAnnouncements(symbol, reason = '巨潮资讯公告接口暂未返回数据。') {
  const meta = getMeta(symbol);
  return {
    symbol,
    items: [
      {
        title: `${meta.name}公告监控`,
        type: '巨潮公告层占位',
        date: new Date().toISOString().slice(0, 10),
        summary: '后续可接巨潮资讯，监控财报、减持、回购、重大合同和风险提示。'
      }
    ],
    source: '巨潮资讯 / structured-fallback',
    note: reason
  };
}

function localConviction(payload) {
  const symbol = String(payload?.symbol || payload?.market?.symbol || '000000').replace('.SH', '').replace('.SZ', '');
  const meta = getMeta(symbol);
  const score = Math.round(pseudo(symbol, 55, 82));
  return {
    conviction_score: score,
    view: score >= 75 ? 'Watchlist / Moderately Bullish' : 'Neutral / Watchlist',
    market_regime: `${meta.industry}主题观察期`,
    factor_scores: {
      quote_layer: Math.round(pseudo(symbol, 48, 78)),
      research_layer: Math.round(pseudo(symbol, 45, 82)),
      signal_layer: Math.round(pseudo(symbol, 42, 76)),
      news_layer: Math.round(pseudo(symbol, 50, 80)),
      announcement_layer: Math.round(pseudo(symbol, 46, 74)),
      valuation: Math.round(pseudo(symbol, 38, 68))
    },
    bull_case: [
      `${meta.name}属于${meta.industry}，具备${meta.theme}相关观察价值。`,
      '行情层、信号层、研报层和公告层已形成基础数据框架，可继续接入实时数据增强判断。',
      '如果资金流和行业排名持续改善，可提高观察优先级。'
    ],
    bear_case: [
      '当前部分数据仍来自结构化fallback，不能替代真实研报和公告核验。',
      '若估值偏高、资金流转弱或公告出现风险，应降低conviction。'
    ],
    final_summary: `${meta.name}当前适合进入观察池。后续应重点验证：资金流是否持续、行业热度是否扩散、研报预期是否上修、公告是否存在风险。`,
    risk_warning: '仅用于研究和教育演示，不构成投资建议。'
  };
}

async function fetchTencentQuote(symbol) {
  const marketSymbol = toMarketSymbol(symbol);
  const url = `https://qt.gtimg.cn/q=${marketSymbol}`;
  const r = await fetch(url, {
    headers: { 'user-agent': 'Mozilla/5.0' }
  });
  const text = await r.text();
  const match = text.match(/="(.+)";?$/);
  if (!match) throw new Error('Tencent quote parse failed');
  const parts = match[1].split('~');

  return {
    symbol,
    name: parts[1] || getMeta(symbol).name,
    price: Number(parts[3]) || null,
    previous_close: Number(parts[4]) || null,
    open: Number(parts[5]) || null,
    volume: Number(parts[6]) || null,
    high: Number(parts[33]) || null,
    low: Number(parts[34]) || null,
    turnover_rate: Number(parts[38]) || null,
    pe: Number(parts[39]) || null,
    pb: Number(parts[46]) || null,
    source: '腾讯财经 qt.gtimg.cn'
  };
}

async function fetchEastmoneyQuote(symbol) {
  const fields = [
    'f43','f44','f45','f46','f47','f48','f57','f58','f60',
    'f116','f117','f162','f167','f168','f169','f170'
  ].join(',');

  const url = `https://push2.eastmoney.com/api/qt/stock/get?secid=${toSecid(symbol)}&fields=${fields}`;
  const r = await fetch(url, { headers: { 'user-agent': 'Mozilla/5.0' } });
  const data = await r.json();
  const d = data?.data || {};
  if (!d || Object.keys(d).length === 0) throw new Error('Eastmoney returned empty data');

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

  return {
    symbol,
    name: d.f58 || getMeta(symbol).name,
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
    source: '东方财富 push2'
  };
}

async function handleHealth(req, res) {
  return send(res, 200, {
    name: 'AI Conviction Engine',
    status: 'ok',
    runtime: 'vercel-node',
    api: 'single-function',
    sources: ['mootdx(外部Python层)', '腾讯财经', 'akshare(外部Python层)', 'iwencai(需Key)', '东方财富PDF', '同花顺', '百度股市通', '巨潮']
  });
}

async function handleMarketQuote(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    const eastmoney = await fetchEastmoneyQuote(symbol);
    if (eastmoney.price) return send(res, 200, eastmoney);
  } catch {}

  try {
    const tencent = await fetchTencentQuote(symbol);
    if (tencent.price) return send(res, 200, tencent);
  } catch (error) {
    return send(res, 200, demoQuote(symbol, String(error.message || error)));
  }

  return send(res, 200, demoQuote(symbol, 'All quote sources returned empty.'));
}

async function handleMarketKline(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  return send(res, 200, {
    symbol,
    items: [],
    source: 'mootdx / akshare external-python-layer placeholder',
    note: 'K线层建议使用mootdx或akshare放到Railway/Render/VPS后端；Vercel Node仅保留入口。'
  });
}

async function handleResearchReports(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });
  return send(res, 200, demoResearch(symbol));
}

async function handleSignalsOverview(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });
  return send(res, 200, demoSignals(symbol));
}

async function handleGlobalNews(req, res) {
  return send(res, 200, {
    items: [],
    source: '腾讯财经 / 百度股市通 placeholder',
    note: '按图中结构，此处不再默认使用Finnhub。后续可接腾讯财经HTTP或百度股市通。'
  });
}

async function handleStockNews(req, res) {
  const symbol = getSymbol(req);
  return send(res, 200, demoNews(symbol));
}

async function handleAnnouncements(req, res) {
  const symbol = getSymbol(req);
  return send(res, 200, demoAnnouncements(symbol));
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
  if (!apiKey) return send(res, 200, localConviction(payload));

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
            content: '你是一个A股AI投研决策引擎。你不是荐股机器人，不给确定性买卖建议。你基于行情层、研报层、信号层、新闻层、公告层输出可解释的 Conviction 分析。必须输出JSON。'
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
      return send(res, 200, { ...localConviction(payload), openai_error: data.error?.message || 'OpenAI request failed' });
    }

    try {
      return send(res, 200, JSON.parse(text));
    } catch {
      return send(res, 200, { ...localConviction(payload), raw_text: text });
    }
  } catch (error) {
    return send(res, 200, { ...localConviction(payload), error: String(error.message || error) });
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
    if (path === '/api/signals/money-flow') return handlePlaceholder(req, res, '同花顺/东方财富资金流');
    if (path === '/api/signals/northbound') return handlePlaceholder(req, res, '北向资金');
    if (path === '/api/signals/dragon-tiger') return handlePlaceholder(req, res, '龙虎榜');
    if (path === '/api/signals/sector-ranking') return handlePlaceholder(req, res, '行业排名');

    if (path === '/api/news/global') return handleGlobalNews(req, res);
    if (path === '/api/news/stock') return handleStockNews(req, res);
    if (path === '/api/news/latest') return handlePlaceholder(req, res, '腾讯财经/百度股市通新闻');

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
