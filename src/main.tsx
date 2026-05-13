import React from 'react'
import ReactDOM from 'react-dom/client'
import { Activity, Newspaper, FileText, Brain, Radio, BarChart3, Search } from 'lucide-react'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts'
import './styles.css'

const API_BASE = import.meta.env.VITE_API_BASE || ''

type Json = Record<string, any>

type StockOption = {
  symbol: string
  name: string
  py: string
  market?: string
}

const STOCK_OPTIONS: StockOption[] = [
  { symbol: '600519', name: '贵州茅台', py: 'gzmt', market: 'SH' },
  { symbol: '000858', name: '五粮液', py: 'wly', market: 'SZ' },
  { symbol: '601318', name: '中国平安', py: 'zgpa', market: 'SH' },
  { symbol: '600036', name: '招商银行', py: 'zsyh', market: 'SH' },
  { symbol: '601899', name: '紫金矿业', py: 'zjky', market: 'SH' },
  { symbol: '600276', name: '恒瑞医药', py: 'hryy', market: 'SH' },
  { symbol: '300750', name: '宁德时代', py: 'ndsd', market: 'SZ' },
  { symbol: '002594', name: '比亚迪', py: 'byd', market: 'SZ' },
  { symbol: '000333', name: '美的集团', py: 'mdjt', market: 'SZ' },
  { symbol: '600900', name: '长江电力', py: 'cjdl', market: 'SH' },
  { symbol: '601012', name: '隆基绿能', py: 'ljln', market: 'SH' },
  { symbol: '000001', name: '平安银行', py: 'payh', market: 'SZ' },
  { symbol: '600030', name: '中信证券', py: 'zxzq', market: 'SH' },
  { symbol: '300059', name: '东方财富', py: 'dfcf', market: 'SZ' },
  { symbol: '688981', name: '中芯国际', py: 'zxgj', market: 'SH' },
  { symbol: '000977', name: '浪潮信息', py: 'lcxx', market: 'SZ' },
  { symbol: '002415', name: '海康威视', py: 'hkws', market: 'SZ' },
  { symbol: '002626', name: '金达威', py: 'jdw', market: 'SZ' },
  { symbol: '600585', name: '海螺水泥', py: 'hlsn', market: 'SH' },
  { symbol: '600309', name: '万华化学', py: 'whhx', market: 'SH' },
  { symbol: '603259', name: '药明康德', py: 'ymkd', market: 'SH' },
  { symbol: '600887', name: '伊利股份', py: 'ylgf', market: 'SH' },
  { symbol: '000063', name: '中兴通讯', py: 'zxtx', market: 'SZ' },
  { symbol: '600050', name: '中国联通', py: 'zglt', market: 'SH' },
  { symbol: '601398', name: '工商银行', py: 'gsyh', market: 'SH' },
  { symbol: '601857', name: '中国石油', py: 'zgsy', market: 'SH' },
]

async function getJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

async function postJson(path: string, body: Json) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

function safeArray(value: any): string[] {
  if (Array.isArray(value)) return value.map((x) => String(x))
  if (typeof value === 'string' && value.trim()) return [value]
  return []
}

function ensureArray(value: any): any[] {
  return Array.isArray(value) ? value : []
}

function safeText(value: any, fallback = '--') {
  if (value === null || value === undefined || value === '') return fallback
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function safeNumber(value: any, fallback = '--') {
  const n = Number(value)
  return Number.isFinite(n) ? String(n) : fallback
}

function dataStatusLabel(data: any) {
  const status = data?.data_status || data?.status
  const source = safeText(data?.source, 'unknown')

  if (status === 'real' || data?.is_fallback === false) {
    return { text: `真实数据 · ${source}`, className: 'status-real' }
  }

  if (status === 'placeholder') {
    return { text: `接口预留 · ${source}`, className: 'status-placeholder' }
  }

  if (status === 'ai-generated') {
    return { text: `AI生成 · ${source}`, className: 'status-ai' }
  }

  return { text: `Fallback占位 · ${source}`, className: 'status-fallback' }
}

function DataStatus({ data }: { data: any }) {
  const s = dataStatusLabel(data)
  return <span className={`data-status ${s.className}`}>{s.text}</span>
}

function scoreToRadar(factorScores: any) {
  if (!factorScores || typeof factorScores !== 'object' || Array.isArray(factorScores)) {
    return []
  }

  return Object.entries(factorScores)
    .map(([name, value]) => ({
      factor: String(name).replaceAll('_', ' '),
      score: Number(value || 0),
    }))
    .filter((x) => Number.isFinite(x.score))
}

function matchStocks(input: string) {
  const raw = input.trim()
  const q = raw.toLowerCase()
  if (!q) return STOCK_OPTIONS.slice(0, 8)

  const matched = STOCK_OPTIONS
    .filter((s) =>
      s.symbol.includes(q) ||
      s.name.includes(raw) ||
      s.py.includes(q) ||
      `${s.name}${s.py}${s.symbol}`.toLowerCase().includes(q)
    )
    .slice(0, 8)

  if (/^\d{6}$/.test(raw) && !matched.some((s) => s.symbol === raw)) {
    matched.unshift({
      symbol: raw,
      name: `A股代码 ${raw}`,
      py: raw,
      market: raw.startsWith('6') ? 'SH' : 'SZ'
    })
  }

  return matched
}

async function searchStocks(query: string): Promise<StockOption[]> {
  const q = query.trim()
  if (!q) return matchStocks(q)

  try {
    const data = await getJson(`/api/search/stocks?q=${encodeURIComponent(q)}`)
    const items = Array.isArray(data.items) ? data.items : []
    return items.map((x: any) => ({
      symbol: String(x.symbol || ''),
      name: String(x.name || x.symbol || ''),
      py: String(x.py || ''),
      market: String(x.market || '')
    })).filter((x: StockOption) => x.symbol)
  } catch (error) {
    console.error('search failed', error)
    return matchStocks(q)
  }
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; message: string }> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true, message: error?.message || 'Unknown frontend error' }
  }

  componentDidCatch(error: any) {
    console.error('Frontend crashed:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="app">
          <div className="error">
            <strong>前端渲染出错，但页面没有黑屏。</strong>
            <pre>{this.state.message}</pre>
            <p>请刷新页面，或检查 API 返回的数据格式。</p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

function LayerCard(props: {
  icon: React.ReactNode
  title: string
  subtitle: string
  children: React.ReactNode
}) {
  return (
    <section className="layer-card">
      <div className="layer-header">
        <div className="layer-icon">{props.icon}</div>
        <div>
          <h2>{props.title}</h2>
          <p>{props.subtitle}</p>
        </div>
      </div>
      {props.children}
    </section>
  )
}

function JsonBlock({ data }: { data: any }) {
  return <pre className="json-block">{JSON.stringify(data ?? {}, null, 2)}</pre>
}

function ResearchPanel({ research }: { research: Json | null }) {
  const reports = ensureArray(research?.reports)
  const forecasts = ensureArray(research?.forecasts)
  const hasData = reports.length > 0 || forecasts.length > 0

  if (!research) return <p className="muted">暂无数据</p>

  if (!hasData) {
    return (
      <div className="empty-card">
        <DataStatus data={research} />
        <strong>暂无研报数据</strong>
        <p>{safeText(research.note, '当前数据源未返回研报或EPS预测。')}</p>
        <span>Source: {safeText(research.source, 'placeholder')}</span>
      </div>
    )
  }

  return (
    <div className="research-list">
      <DataStatus data={research} />
      {reports.slice(0, 3).map((r, i) => (
        <div className="mini-card" key={`report-${i}`}>
          <strong>{safeText(r.title || r.report_title || r.name, '研报')}</strong>
          <p>{safeText(r.org_name || r.broker || r.source || r.author, '机构信息暂无')}</p>
        </div>
      ))}

      {forecasts.slice(0, 3).map((f, i) => (
        <div className="mini-card" key={`forecast-${i}`}>
          <strong>{safeText(f.type || f.end_date || '业绩预告')}</strong>
          <p>{safeText(f.summary || f.p_change_min || f.net_profit_min, '暂无摘要')}</p>
        </div>
      ))}
    </div>
  )
}


function SimpleItemsPanel({ data, emptyTitle }: { data: Json | null, emptyTitle: string }) {
  const items = ensureArray(data?.items)
  if (!data) return <p className="muted">暂无数据</p>
  if (!items.length) {
    return (
      <div className="empty-card">
        <DataStatus data={data} />
        <strong>{emptyTitle}</strong>
        <p>{safeText(data.note, '当前接口没有返回数据。')}</p>
        <span>Source: {safeText(data.source, 'placeholder')}</span>
      </div>
    )
  }

  return (
    <div className="research-list">
      <DataStatus data={research} />
      {items.slice(0, 3).map((x, i) => (
        <div className="mini-card" key={i}>
          <strong>{safeText(x.title || x.label || x.type || '数据项')}</strong>
          <p>{safeText(x.summary || x.value || x.sentiment || x.signal || x.source || '暂无摘要')}</p>
        </div>
      ))}
    </div>
  )
}

function SignalPanel({ signals }: { signals: Json | null }) {
  if (!signals) return <p className="muted">暂无数据</p>
  const money = ensureArray(signals?.money_flow?.items)
  const sector = ensureArray(signals?.sector_ranking?.items)
  const all = [...money, ...sector]

  if (!all.length) {
    return (
      <div className="empty-card">
        <DataStatus data={signals} />
        <strong>暂无信号数据</strong>
        <p>{safeText(signals.note, '当前资金流/行业接口没有返回数据。')}</p>
        <span>Source: {safeText(signals?.money_flow?.source, 'placeholder')}</span>
      </div>
    )
  }

  return (
    <div className="research-list">
      <DataStatus data={research} />
      {all.slice(0, 4).map((x, i) => (
        <div className="mini-card" key={i}>
          <strong>{safeText(x.label || x.trade_date || '信号')}</strong>
          <p>{safeText(x.value || x.net_mf_amount || x.signal || '暂无说明')}</p>
        </div>
      ))}
    </div>
  )
}

function App() {
  const [symbol, setSymbol] = React.useState('600519')
  const [searchText, setSearchText] = React.useState('贵州茅台')
  const [suggestions, setSuggestions] = React.useState<StockOption[]>([])
  const [showDropdown, setShowDropdown] = React.useState(false)
  const [loading, setLoading] = React.useState(false)
  const [market, setMarket] = React.useState<Json | null>(null)
  const [research, setResearch] = React.useState<Json | null>(null)
  const [signals, setSignals] = React.useState<Json | null>(null)
  const [news, setNews] = React.useState<Json | null>(null)
  const [announcements, setAnnouncements] = React.useState<Json | null>(null)
  const [ai, setAi] = React.useState<Json | null>(null)
  const [error, setError] = React.useState<string>('')

  async function handleSearchChange(value: string) {
    setSearchText(value)
    setShowDropdown(true)

    const results = await searchStocks(value)
    setSuggestions(results)

    const exact = results.find(
      (s) => s.symbol === value.trim() || s.name === value.trim() || s.py === value.trim().toLowerCase()
    )
    if (exact) setSymbol(exact.symbol)
    else if (/^\d{6}$/.test(value.trim())) setSymbol(value.trim())
  }

  function selectStock(stock: StockOption) {
    setSymbol(stock.symbol)
    setSearchText(stock.name)
    setSuggestions([])
    setShowDropdown(false)
    setTimeout(() => run(stock.symbol), 0)
  }

  async function run(nextSymbol?: string) {
    const activeSymbol = nextSymbol || symbol
    setLoading(true)
    setError('')
    setAi(null)

    try {
      const [m, r, s, n, a] = await Promise.all([
        getJson(`/api/market/quote?symbol=${encodeURIComponent(activeSymbol)}`),
        getJson(`/api/research/reports?symbol=${encodeURIComponent(activeSymbol)}&limit=8`),
        getJson(`/api/signals/overview?symbol=${encodeURIComponent(activeSymbol)}`),
        getJson(`/api/news/stock?symbol=${encodeURIComponent(activeSymbol)}&limit=8`),
        getJson(`/api/announcements/stock?symbol=${encodeURIComponent(activeSymbol)}&limit=8`),
      ])

      setMarket(m)
      setResearch(r)
      setSignals(s)
      setNews(n)
      setAnnouncements(a)

      const aiResult = await postJson('/api/ai/conviction', {
        symbol: activeSymbol,
        market: m,
        research: r,
        signals: s,
        news: n,
        announcements: a,
      })

      setAi(aiResult || {})
    } catch (e: any) {
      console.error(e)
      setError(e.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    searchStocks(searchText).then(setSuggestions)
    run()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const radarData = scoreToRadar(ai?.factor_scores)
  const bullCase = safeArray(ai?.bull_case)
  const bearCase = safeArray(ai?.bear_case)

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">A-STOCK DATA · AI RESEARCH</p>
          <h1>AI Conviction Engine</h1>
          <p className="hero-copy">
            行情层 / 研报层 / 信号层 / 新闻层 / 公告层 / AI总结层
          </p>
        </div>

        <div className="search-box">
          <div className="search-input-wrap">
            <Search size={16} className="search-icon" />
            <input
              value={searchText}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={async () => {
                setSuggestions(await searchStocks(searchText))
                setShowDropdown(true)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  const raw = searchText.trim()
                  if (/^\d{6}$/.test(raw)) {
                    setSymbol(raw)
                    run(raw)
                    setShowDropdown(false)
                  } else if (suggestions[0]) {
                    selectStock(suggestions[0])
                  }
                }
              }}
              onBlur={() => setTimeout(() => setShowDropdown(false), 160)}
              placeholder="搜索代码 / 中文 / 拼音首字母，例如 600519、贵州茅台、gzmt、002626"
            />

            {showDropdown && suggestions.length > 0 && (
              <div className="search-dropdown">
                {suggestions.map((s) => (
                  <button key={s.symbol} type="button" onMouseDown={() => selectStock(s)}>
                    <span>
                      <strong>{s.name}</strong>
                      <em>{s.py}</em>
                    </span>
                    <b>{s.symbol}</b>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button onClick={() => run()} disabled={loading}>
            {loading ? '分析中...' : '运行分析'}
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <nav className="tabs">
        <a href="#market">行情层</a>
        <a href="#research">研报层</a>
        <a href="#signals">信号层</a>
        <a href="#news">新闻层</a>
        <a href="#announcements">公告层</a>
        <a href="#summary">AI总结</a>
      </nav>

      <main className="grid">
        <LayerCard
          icon={<Activity size={20} />}
          title="行情层"
          subtitle="K线、报价、估值、成交额、换手率"
        >
          <div id="market" />
          {market ? (
            <>
            <DataStatus data={market} />
            <div className="quote">
              <div>
                <span className="muted">股票</span>
                <strong>{safeText(market.name || market.symbol)}</strong>
              </div>
              <div>
                <span className="muted">价格</span>
                <strong>{safeNumber(market.price)}</strong>
              </div>
              <div>
                <span className="muted">涨跌幅</span>
                <strong>{safeNumber(market.change_pct)}%</strong>
              </div>
              <div>
                <span className="muted">来源</span>
                <strong>{safeText(market.source)}</strong>
              </div>
            </div>
            </>
          ) : <p className="muted">暂无数据</p>}
        </LayerCard>

        <LayerCard
          icon={<FileText size={20} />}
          title="研报层"
          subtitle="券商研报、PDF、EPS预测、一致预期"
        >
          <div id="research" />
          <ResearchPanel research={research} />
        </LayerCard>

        <LayerCard
          icon={<BarChart3 size={20} />}
          title="信号层"
          subtitle="北向资金、龙虎榜、行业排名、资金流"
        >
          <div id="signals" />
          <SignalPanel signals={signals} />
        </LayerCard>

        <LayerCard
          icon={<Newspaper size={20} />}
          title="新闻层"
          subtitle="快讯、个股新闻、AI新闻摘要"
        >
          <div id="news" />
          <SimpleItemsPanel data={news} emptyTitle="暂无新闻数据" />
        </LayerCard>

        <LayerCard
          icon={<Radio size={20} />}
          title="公告层"
          subtitle="公司公告、财报、交易所公告"
        >
          <div id="announcements" />
          <SimpleItemsPanel data={announcements} emptyTitle="暂无公告数据" />
        </LayerCard>

        <LayerCard
          icon={<Brain size={20} />}
          title="AI总结层"
          subtitle="Conviction Score、Bull Case、Bear Case、风险提示"
        >
          <div id="summary" />
          {ai ? (
            <div className="ai-summary">
              <DataStatus data={ai} />
              <div className="score-row">
                <div>
                  <p className="muted">Conviction Score</p>
                  <div className="score">{safeNumber(ai.conviction_score, 'N/A')}</div>
                </div>
                <div>
                  <p className="muted">View</p>
                  <h3>{safeText(ai.view, 'Watchlist')}</h3>
                  <p>{safeText(ai.market_regime, 'Unknown')}</p>
                </div>
              </div>

              {radarData.length > 0 && (
                <div className="radar-wrap">
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={radarData} outerRadius="72%">
                      <PolarGrid stroke="#52525b" radialLines={true} />
                      <PolarAngleAxis dataKey="factor" tick={{ fill: '#d4d4d8', fontSize: 12 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#71717a', fontSize: 10 }} />
                      <Radar
                        name="Conviction"
                        dataKey="score"
                        stroke="#ff5b24"
                        strokeWidth={3}
                        fill="#ff5b24"
                        fillOpacity={0.38}
                        dot={{ fill: '#fff', r: 3 }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="cases">
                <div>
                  <h4>Bull Case</h4>
                  {bullCase.length > 0 ? (
                    <ul>{bullCase.map((x, i) => <li key={i}>{x}</li>)}</ul>
                  ) : <p className="muted">暂无正面理由</p>}
                </div>
                <div>
                  <h4>Bear Case</h4>
                  {bearCase.length > 0 ? (
                    <ul>{bearCase.map((x, i) => <li key={i}>{x}</li>)}</ul>
                  ) : <p className="muted">暂无风险理由</p>}
                </div>
              </div>

              <p className="final">{safeText(ai.final_summary, '暂无总结')}</p>
              <p className="risk">{safeText(ai.risk_warning, '仅用于研究和教育演示，不构成投资建议。')}</p>
            </div>
          ) : <p className="muted">运行后生成 AI 总结。</p>}
        </LayerCard>
      </main>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
)
