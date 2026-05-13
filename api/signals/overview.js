import { send, getSymbol, toTsCode, tushare } from '../_utils.js';

export default async function handler(req, res) {
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
