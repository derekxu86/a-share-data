import { send, getSymbol, toTsCode, tushare } from '../_utils.js';

export default async function handler(req, res) {
  const symbol = getSymbol(req);
  if (!symbol) return send(res, 400, { error: 'Missing symbol' });

  try {
    // Tushare forecast can provide earnings forecast data if permission allows.
    const forecast = await tushare(
      'forecast',
      { ts_code: toTsCode(symbol), limit: 10 },
      'ts_code,ann_date,end_date,type,p_change_min,p_change_max,net_profit_min,net_profit_max,summary'
    );

    return send(res, 200, {
      symbol,
      reports: [],
      forecasts: forecast.ok ? forecast.items : [],
      source: forecast.ok ? 'tushare.forecast' : 'placeholder',
      note: forecast.ok ? 'Research PDF layer can be added later via Eastmoney/CNInfo.' : forecast.error
    });
  } catch (error) {
    return send(res, 200, { symbol, reports: [], forecasts: [], source: 'safe-fallback', error: String(error.message || error) });
  }
}
