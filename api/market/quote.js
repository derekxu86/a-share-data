import { send, getSymbol, toSecid, toTsCode, tushare } from '../_utils.js';

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

export default async function handler(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    const fields = [
      'f43','f44','f45','f46','f47','f48','f57','f58','f60',
      'f116','f117','f162','f167','f168','f169','f170'
    ].join(',');

    const url = `https://push2.eastmoney.com/api/qt/stock/get?secid=${toSecid(symbol)}&fields=${fields}`;
    const r = await fetch(url, {
      headers: { 'user-agent': 'Mozilla/5.0' }
    });
    const data = await r.json();
    const d = data?.data || {};

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

    // Optional Tushare daily_basic enrichment.
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
