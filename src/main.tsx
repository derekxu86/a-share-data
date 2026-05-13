import React from 'react'
import ReactDOM from 'react-dom/client'
import { Activity, Newspaper, FileText, Brain, Radio, BarChart3 } from 'lucide-react'
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import './styles.css'

const API_BASE = import.meta.env.VITE_API_BASE || ''

type Json = Record<string, any>

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

function scoreToRadar(factorScores: Json = {}) {
  return Object.entries(factorScores).map(([name, value]) => ({
    factor: name.replaceAll('_', ' '),
    score: Number(value || 0),
  }))
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
  return <pre className="json-block">{JSON.stringify(data, null, 2)}</pre>
}

function App() {
  const [symbol, setSymbol] = React.useState('600519')
  const [loading, setLoading] = React.useState(false)
  const [market, setMarket] = React.useState<Json | null>(null)
  const [research, setResearch] = React.useState<Json | null>(null)
  const [signals, setSignals] = React.useState<Json | null>(null)
  const [news, setNews] = React.useState<Json | null>(null)
  const [announcements, setAnnouncements] = React.useState<Json | null>(null)
  const [ai, setAi] = React.useState<Json | null>(null)
  const [error, setError] = React.useState<string>('')

  async function run() {
    setLoading(true)
    setError('')
    setAi(null)
    try {
      const [m, r, s, n, a] = await Promise.all([
        getJson(`/api/market/quote?symbol=${symbol}`),
        getJson(`/api/research/reports?symbol=${symbol}&limit=8`),
        getJson(`/api/signals/overview?symbol=${symbol}`),
        getJson(`/api/news/stock?symbol=${symbol}&limit=8`),
        getJson(`/api/announcements/stock?symbol=${symbol}&limit=8`),
      ])
      setMarket(m)
      setResearch(r)
      setSignals(s)
      setNews(n)
      setAnnouncements(a)

      const aiResult = await postJson('/api/ai/conviction', {
        symbol,
        market: m,
        research: r,
        signals: s,
        news: n,
        announcements: a,
      })
      setAi(aiResult)
    } catch (e: any) {
      setError(e.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  React.useEffect(() => {
    run()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const radarData = scoreToRadar(ai?.factor_scores)

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
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="输入A股代码，例如 600519"
          />
          <button onClick={run} disabled={loading}>
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
            <div className="quote">
              <div>
                <span className="muted">股票</span>
                <strong>{market.name || market.symbol}</strong>
              </div>
              <div>
                <span className="muted">价格</span>
                <strong>{market.price}</strong>
              </div>
              <div>
                <span className="muted">涨跌幅</span>
                <strong>{market.change_pct}%</strong>
              </div>
              <div>
                <span className="muted">来源</span>
                <strong>{market.source}</strong>
              </div>
            </div>
          ) : <p className="muted">暂无数据</p>}
        </LayerCard>

        <LayerCard
          icon={<FileText size={20} />}
          title="研报层"
          subtitle="券商研报、PDF、EPS预测、一致预期"
        >
          <div id="research" />
          <JsonBlock data={research?.reports?.slice?.(0, 3) || research} />
        </LayerCard>

        <LayerCard
          icon={<BarChart3 size={20} />}
          title="信号层"
          subtitle="北向资金、龙虎榜、行业排名、资金流"
        >
          <div id="signals" />
          <JsonBlock data={{
            money_flow_source: signals?.money_flow?.source,
            northbound_source: signals?.northbound?.source,
            dragon_tiger_count: signals?.dragon_tiger?.items?.length,
            sector_count: signals?.sector_ranking?.items?.length
          }} />
        </LayerCard>

        <LayerCard
          icon={<Newspaper size={20} />}
          title="新闻层"
          subtitle="快讯、个股新闻、AI新闻摘要"
        >
          <div id="news" />
          <JsonBlock data={news?.items?.slice?.(0, 3) || news} />
        </LayerCard>

        <LayerCard
          icon={<Radio size={20} />}
          title="公告层"
          subtitle="公司公告、财报、交易所公告"
        >
          <div id="announcements" />
          <JsonBlock data={announcements?.items?.slice?.(0, 3) || announcements} />
        </LayerCard>

        <LayerCard
          icon={<Brain size={20} />}
          title="AI总结层"
          subtitle="Conviction Score、Bull Case、Bear Case、风险提示"
        >
          <div id="summary" />
          {ai ? (
            <div className="ai-summary">
              <div className="score-row">
                <div>
                  <p className="muted">Conviction Score</p>
                  <div className="score">{ai.conviction_score}</div>
                </div>
                <div>
                  <p className="muted">View</p>
                  <h3>{ai.view}</h3>
                  <p>{ai.market_regime}</p>
                </div>
              </div>

              {radarData.length > 0 && (
                <div className="radar-wrap">
                  <ResponsiveContainer width="100%" height={260}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="factor" />
                      <Radar dataKey="score" fillOpacity={0.3} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              )}

              <div className="cases">
                <div>
                  <h4>Bull Case</h4>
                  <ul>{ai.bull_case?.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
                </div>
                <div>
                  <h4>Bear Case</h4>
                  <ul>{ai.bear_case?.map((x: string, i: number) => <li key={i}>{x}</li>)}</ul>
                </div>
              </div>

              <p className="final">{ai.final_summary}</p>
              <p className="risk">{ai.risk_warning}</p>
            </div>
          ) : <p className="muted">运行后生成 AI 总结。</p>}
        </LayerCard>
      </main>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />)
