export function send(res, status, payload) {
  res.status(status).setHeader('content-type', 'application/json; charset=utf-8');
  res.setHeader('cache-control', 's-maxage=60, stale-while-revalidate=300');
  res.json(payload);
}

export function getSymbol(req) {
  return String(req.query.symbol || '').trim().toUpperCase().replace('.SH', '').replace('.SZ', '');
}

export function toSecid(symbol) {
  const code = String(symbol || '').replace('.SH', '').replace('.SZ', '');
  if (code.startsWith('6')) return `1.${code}`;
  return `0.${code}`;
}

export function toTsCode(symbol) {
  const code = String(symbol || '').replace('.SH', '').replace('.SZ', '');
  if (code.startsWith('6')) return `${code}.SH`;
  return `${code}.SZ`;
}

export async function tushare(apiName, params = {}, fields = '') {
  const token = process.env.TUSHARE_TOKEN;
  if (!token) {
    return { ok: false, error: 'TUSHARE_TOKEN not configured', items: [] };
  }

  const response = await fetch('https://api.tushare.pro', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      api_name: apiName,
      token,
      params,
      fields
    })
  });

  const data = await response.json();
  if (!response.ok || data.code !== 0) {
    return { ok: false, error: data.msg || 'Tushare request failed', raw: data, items: [] };
  }

  const columns = data.data?.fields || [];
  const rows = data.data?.items || [];
  const items = rows.map(row => Object.fromEntries(columns.map((c, i) => [c, row[i]])));
  return { ok: true, items, source: `tushare.${apiName}` };
}

export function mock(source, note = 'Data source unavailable. Endpoint returned safe fallback.') {
  return { source, note, items: [] };
}
