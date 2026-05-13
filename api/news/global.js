import { send } from '../_utils.js';

export default async function handler(req, res) {
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
