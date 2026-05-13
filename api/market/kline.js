import { send, getSymbol, toTsCode, tushare } from '../_utils.js';

export default async function handler(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    const data = await tushare(
      'daily',
      { ts_code: toTsCode(symbol), limit: Number(req.query.limit || 120) },
      'ts_code,trade_date,open,high,low,close,vol,amount'
    );

    if (!data.ok) {
      return send(res, 200, { symbol, items: [], source: 'tushare.daily', error: data.error });
    }

    return send(res, 200, {
      symbol,
      items: data.items.reverse(),
      source: 'tushare.daily'
    });
  } catch (error) {
    return send(res, 200, { symbol, items: [], source: 'safe-fallback', error: String(error.message || error) });
  }
}
