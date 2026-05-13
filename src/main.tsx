import React from 'react'
import ReactDOM from 'react-dom/client'
import { Activity, Newspaper, FileText, Brain, Radio, BarChart3, Search } from 'lucide-react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'
import './styles.css'

const API_BASE = ''

async function getJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

async function postJson(path: string, body: any) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

function safeText(v: any, f = '--') { return (v === null || v === undefined || v === '') ? f : String(v) }
function ensureArray(v: any): any[] { return Array.isArray(v) ? v : [] }

function DataStatus({ data }: { data: any }) {
  const status = data?.data_status || data?.status
  const source = safeText(data?.source, 'unknown')
  let cls = 'status-fallback', txt = `Fallback · ${source}`
  if (status === 'real') { cls = 'status-real'; txt = `真实数据 · ${source}` }
  else if (status === 'placeholder') { cls = 'status-placeholder'; txt = `接口预留 · ${source}` }
  else if (status === 'ai-generated') { cls = 'status-ai'; txt = `AI生成 · ${source}` }
  return <span className={`data-status ${cls}`}>{txt}</span>
}

function scoreToRadar(factorScores: any) {
  if (!factorScores || typeof factorScores !== 'object') return []
  return Object.entries(factorScores).map(([name, value]) => ({
    factor: String(name).replaceAll('_', ' '),
    score: Number(value || 0),
  }))
}

function ResearchPanel({ research }: { research: any }) {
  const reports = ensureArray(research?.reports)
  if (!research) return <p className="muted">暂无数据</p>
  return (
    <div className="research-list">
      <DataStatus data={research} />
      {reports.length > 0 ? reports.slice(0, 3).map((r: any, i: number) => (
        <div className="mini-card" key={i}><strong>{safeText(r.title)}</strong><p>{safeText(r.broker)}</p></div>
      )) : <div className="empty-card"><strong>暂无数据</strong><p>{research.note || '接口待接入'}</p></div>}
    </div>
  )
}

function SignalPanel({ signals }: { signals: any }) {
  const items = ensureArray(signals?.money_flow?.items)
  if (!signals) return <p className="muted">暂无数据</p>
  return (
    <div className="research-list">
      <DataStatus data={signals} />
      {items.length > 0 ? items.slice(0, 3).map((x: any, i: number) => (
        <div className="mini-card" key={i}><strong>{safeText(x.label)}</strong><p>{safeText(x.value)}</p></div>
      )) : <div className="empty-card"><strong>暂无数据</strong><p>{signals.note || '信号层开发中'}</p></div>}
    </div>
  )
}

function SimpleItemsPanel({ data, emptyTitle }: { data: any, emptyTitle: string }) {
  const items = ensureArray(data?.items)
  if (!data) return <p className="muted">暂无数据</p>
  return (
    <div className="research-list">
      <DataStatus data={data} />
      {items.length > 0 ? items.slice(0, 3).map((x: any, i: number) => (
        <div className="mini-card" key={i}><strong>{safeText(x.title || x.label)}</strong><p>{safeText(x.summary || x.source)}</p></div>
      )) : <div className="empty-card"><strong>{emptyTitle}</strong><p>{data.note || '暂无内容'}</p></div>}
    </div>
  )
}

function App() {
  const [symbol, setSymbol] = React.useState('600519')
  const [searchText, setSearchText] = React.useState('贵州茅台')
  const [suggestions, setSuggestions] = React.useState<any[]>([])
  const [showDropdown, setShowDropdown] = React.useState(false)
  const [loading, setLoading] = React.useState(false)
  const [market, setMarket] = React.useState<any>(null)
  const [research, setResearch] = React.useState<any>(null)
  const [signals, setSignals] = React.useState<any>(null)
  const [news, setNews] = React.useState<any>(null)
  const [announcements, setAnnouncements] = React.useState<any>(null)
  const [ai, setAi] = React.useState<any>(null)

  async function run(s?: string) {
    const sym = s || symbol; setLoading(true)
    try {
      const [m, r, sig, n, a] = await Promise.all([
        getJson(`/api/market/quote?symbol=${sym}`),
        getJson(`/api/research/reports?symbol=${sym}`),
        getJson(`/api/signals/overview?symbol=${sym}`),
        getJson(`/api/news/stock?symbol=${sym}`),
        getJson(`/api/announcements/stock?symbol=${sym}`),
      ])
      setMarket(m); setResearch(r); setSignals(sig); setNews(n); setAnnouncements(a)
      const res = await postJson('/api/ai/conviction', { symbol: sym, market: m, research: r, signals: sig, news: n, announcements: a })
      setAi(res)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  React.useEffect(() => { run() }, [])

  const radarData = scoreToRadar(ai?.factor_scores)
  const bullCase = ensureArray(ai?.bull_case)
  const bearCase = ensureArray(ai?.bear_case)

  return (
    <div className="app">
      <header className="hero">
        <div><p className="eyebrow">A-STOCK DATA · AI RESEARCH</p><h1>AI Conviction Engine</h1></div>
        <div className="search-box">
          <div className="search-input-wrap">
            <Search size={16} className="search-icon" />
            <input value={searchText} onChange={async (e) => {
              setSearchText(e.target.value); setShowDropdown(true)
              const d = await getJson(`/api/search/stocks?q=${e.target.value}`)
              setSuggestions(d.items || [])
            }} onFocus={() => setShowDropdown(true)} placeholder="搜索代码/名称" />
            {showDropdown && suggestions.length > 0 && (
              <div className="search-dropdown">
                {suggestions.map((s: any) => (
                  <button key={s.symbol} onMouseDown={() => { setSymbol(s.symbol); setSearchText(s.name); setShowDropdown(false); run(s.symbol) }}>
                    <span><strong>{s.name}</strong><em>{s.py}</em></span><b>{s.symbol}</b>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => run()} disabled={loading}>{loading ? '分析中...' : '运行分析'}</button>
        </div>
      </header>

      <main className="grid">
        <section className="layer-card">
          <div className="layer-header"><Activity className="layer-icon" /><div><h2>行情层</h2><p>实时报价与涨跌幅</p></div></div>
          {market && <><DataStatus data={market} /><div className="quote"><div><span className="muted">股票</span><strong>{market.name}</strong></div><div><span className="muted">价格</span><strong>{market.price}</strong></div><div><span className="muted">涨跌幅</span><strong>{market.change_pct}%</strong></div></div></>}
        </section>
        <section className="layer-card">
          <div className="layer-header"><FileText className="layer-icon" /><div><h2>研报层</h2><p>券商深度研究</p></div></div>
          <ResearchPanel research={research} />
        </section>
        <section className="layer-card">
          <div className="layer-header"><BarChart3 className="layer-icon" /><div><h2>信号层</h2><p>资金流向与排名</p></div></div>
          <SignalPanel signals={signals} />
        </section>
        <section className="layer-card">
          <div className="layer-header"><Newspaper className="layer-icon" /><div><h2>新闻层</h2><p>个股实时资讯</p></div></div>
          <SimpleItemsPanel data={news} emptyTitle="暂无新闻" />
        </section>
        <section className="layer-card">
          <div className="layer-header"><Radio className="layer-icon" /><div><h2>公告层</h2><p>上市公司公告</p></div></div>
          <SimpleItemsPanel data={announcements} emptyTitle="暂无公告" />
        </section>
        <section className="layer-card" style={{ gridColumn: '1 / -1' }}>
          <div className="layer-header"><Brain className="layer-icon" /><div><h2>AI 总结层</h2><p>智能投资建议</p></div></div>
          {ai && (
            <div className="ai-summary">
              <DataStatus data={ai} />
              <div className="score-row"><div className="score">{ai.conviction_score}</div><div><h3>{ai.view}</h3><p>{ai.market_regime}</p></div></div>
              
              {radarData.length > 0 && (
                <div className="radar-wrap">
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={radarData} outerRadius="72%">
                      <PolarGrid stroke="#52525b" radialLines={true} />
                      <PolarAngleAxis dataKey="factor" tick={{ fill: '#d4d4d8', fontSize: 12 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#71717a', fontSize: 10 }} />
                      <Radar name="Conviction" dataKey="score" stroke="#ff5b24" strokeWidth={3} fill="#ff5b24" fillOpacity={0.38} dot={{ fill: '#fff', r: 3 }} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="cases">
                <div><h4>Bull Case</h4>{bullCase.length > 0 ? <ul>{bullCase.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="muted">暂无正面理由</p>}</div>
                <div><h4>Bear Case</h4>{bearCase.length > 0 ? <ul>{bearCase.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="muted">暂无风险提示</p>}</div>
              </div>

              <p className="final">{ai.final_summary}</p>
              <p className="risk">{ai.risk_warning}</p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />)
