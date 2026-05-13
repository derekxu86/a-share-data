import { send } from '../_utils.js';

export default function handler(req, res) {
  return send(res, 200, {
    items: [],
    source: 'placeholder',
    note: 'A-share latest news layer reserved. Use /api/news/global for Finnhub global news.'
  });
}
