import { send } from '../_utils.js';

export default function handler(req, res) {
  return send(res, 200, {
    items: [],
    source: 'placeholder',
    note: 'This endpoint is reserved for the signal layer. Use /api/signals/overview first.'
  });
}
