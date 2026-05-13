import { send, getSymbol } from '../_utils.js';

export default function handler(req, res) {
  const symbol = getSymbol(req);
  return send(res, 200, {
    symbol,
    items: [],
    source: 'placeholder',
    note: 'A-share stock news layer reserved. Use global news first, or add Eastmoney/Cailianshe endpoint later.'
  });
}
