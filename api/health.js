import { send } from './_utils.js';

export default function handler(req, res) {
  return send(res, 200, {
    name: 'AI Conviction Engine',
    status: 'ok',
    runtime: 'vercel-node',
    api: 'stable'
  });
}
