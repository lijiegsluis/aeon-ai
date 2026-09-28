import { useState, useEffect } from 'react'
import './Intelligence.css'

interface NewsItem {
  id: number
  title: string
  published_at: string
  source: string
  sentiment: string
  summary: string
  url: string
  tickers: string
  urgency?: string
}

interface TelegramStatus {
  connected: boolean
  authorized: boolean | null
  last_error: string | null
  started_at: string | null
  history_window_days: number
  backfilled_count: number | null
  message_count: number
}

interface Signal {
  id: number
  ticker: string
  signal_type: string
  phase: string
  entry_price: number | null
  target_price: number | null
  stop_loss: number | null
  confidence: number
  reasoning: string
  trigger?: string
}

interface CryptoData {
  id: number
  symbol: string
  name: string
  price: number
  change_24h: number
  market_cap: number
  volume_24h: number
  source: string
}

interface SentimentIndicator {
  id: number
  source: string
  indicator_name: string
  value: number
  interpretation: string
  affected_markets: string
  timestamp: string
}

interface InsiderTrade {
  ticker: string
  insider_name: string
  role: string
  transaction_type: string
  shares: number
  price: number
  total_value: number
  date: string
  filing_date: string
  ownership_change: string
  significance: string
  smart_money_signal: string
}

interface AlternativeInsiderData {
  id: number
  source: string
  data_type: string
  ticker?: string
  politician?: string
  chamber?: string
  transaction_type?: string
  amount_range?: string
  trade_date?: string
  disclosure_date?: string
  signal: string
  significance: string
  edge: string
}

interface SmartMoneyNotification {
  id: number
  type: string
  ticker: string
  title: string
  message: string
  significance: string
  timestamp: string
  days_ago?: number
  days_ahead?: number
  action: string
  value?: number
  expected?: boolean
}

interface DailyBrief {
  date: string
  market_regime: string
  primary_catalyst: string
  mega_cap_plays?: Array<{
    ticker: string
    market_cap: string
    action: string
    target: string
    stop: string
    confidence: string
    timeframe: string
    rationale: string
    risks: string
    catalyst: string
    data_sources: string[]
  }>
  large_cap_plays?: Array<{
    ticker: string
    market_cap: string
    action: string
    target: string
    stop: string
    confidence: string
    timeframe: string
    rationale: string
    risks: string
    catalyst: string
    data_sources: string[]
  }>
  mid_cap_opportunities?: Array<{
    ticker: string
    market_cap: string
    action: string
    target: string
    stop: string
    confidence: string
    timeframe: string
    rationale: string
    risks: string
    catalyst: string
    data_sources: string[]
  }>
  event_driven_plays?: Array<{
    ticker: string
    market_cap: string
    action: string
    target: string
    stop: string
    confidence: string
    timeframe: string
    rationale: string
    risks: string
    catalyst: string
    data_sources: string[]
  }>
  sector_plays?: Array<{
    sector: string
    tickers: string[]
    action: string
    rationale: string
    catalyst: string
    data_sources: string[]
  }>
  top_recommendations: Array<{
    ticker: string
    action: string
    target: string
    stop: string
    confidence: string
    timeframe: string
    rationale: string
    risks: string
    data_sources: string[]
  }>
  market_context: {
    key_events_today: string[]
    macro_regime: string
    sector_rotation: string
    volatility_setup: string
    sentiment: string
    news_driven_movers?: string[]
  }
  action_plan: {
    immediate: string[]
    this_week: string[]
    this_month: string[]
  }
  risk_management?: {
    market_risks: string
    position_sizing: string
    hedging: string
    watch_levels: string
  }
}

interface AIPrediction {
  prediction_id: string
  type?: string
  ticker?: string
  sector?: string
  prediction: string
  confidence: number
  timeframe: string
  supporting_signals?: string[]
  supporting_data?: string[]
  historical_precedent?: string
  predicted_outcome?: {
    if_correct?: string
    if_wrong?: string
    if_approved?: string
    if_delayed?: string
    if_rejected?: string
    if_miss_to_3_2?: string
    if_inline_3_3?: string
    if_beat_to_3_4_plus?: string
    expected_value?: string
  }
  predicted_move?: string
  reasoning: string
  adversarial_test?: string
  action: string
  pattern_type?: string
  causal_chain?: string
  contrarian_view?: string
  risk_id?: string
  risk_type?: string
  scenario?: string
  probability?: number
  impact_if_occurs?: string
  early_warning_indicators?: string[]
  hedge?: string
}

interface AIPredictions {
  meta: {
    generated_at: string
    model_version: string
    prediction_horizon: string
    confidence_calibration: string
    total_data_sources: number
    training_data: string
  }
  high_confidence_predictions: AIPrediction[]
  pattern_based_predictions: AIPrediction[]
  causal_predictions: AIPrediction[]
  contrarian_predictions: AIPrediction[]
  black_swan_monitors: AIPrediction[]
  prediction_accuracy_stats: {
    last_30_days: {
      predictions_made: number
      predictions_resolved: number
      correct: number
      accuracy: number
      avg_confidence: number
      calibration_score: number
    }
    by_category: {
      [key: string]: {
        accuracy: number
        n: number
      }
    }
    model_improvements: string[]
  }
  historical_backtest?: {
    status?: string
    note?: string
    methodology?: string
    universe?: string[]
    period?: { start: string; end: string; days: number }
    filings_checked?: number
    signals?: {
      [key: string]: {
        events_found: number
        by_horizon: {
          [horizon: string]: {
            signals_tested: number
            pct_positive: number | null
            avg_return_pct: number | null
          }
        }
        sample_events: Array<{
          ticker: string
          date: string
          insider_or_insiders: string | string[]
          value: number
          returns_by_horizon_pct: { [horizon: string]: number }
        }>
      }
    }
    data_sources?: string
    caveat?: string
    computed_at?: string
  }
}

type ViewType = 'overview' | 'live' | 'signals' | 'insider' | 'telegram' | 'brief' | 'ai-predictions'

function Intelligence() {
  const [view, setView] = useState<ViewType>('overview')
  const [news, setNews] = useState<NewsItem[]>([])
  const [signals, setSignals] = useState<Signal[]>([])
  const [crypto, setCrypto] = useState<CryptoData[]>([])
  const [sentiment, setSentiment] = useState<SentimentIndicator[]>([])
  const [insiderTrades, setInsiderTrades] = useState<InsiderTrade[]>([])
  const [dailyBrief, setDailyBrief] = useState<DailyBrief | null>(null)
  const [aiPredictions, setAiPredictions] = useState<AIPredictions | null>(null)
  const [smartMoneyNotifications, setSmartMoneyNotifications] = useState<{past: SmartMoneyNotification[], future: SmartMoneyNotification[]}>({past: [], future: []})
  const [telegramMessages, setTelegramMessages] = useState<NewsItem[]>([])
  const [telegramStatus, setTelegramStatus] = useState<TelegramStatus | null>(null)
  const [connected, setConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  useEffect(() => {
    fetchAllData()
    const interval = setInterval(fetchAllData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchAllData = async () => {
    try {
      const [dashboardRes, smartMoneyRes, aiPredictionsRes, telegramRes] = await Promise.all([
        fetch('http://localhost:8001/api/dashboard'),
        fetch('http://localhost:8001/api/smart-money/notifications'),
        fetch('http://localhost:8001/api/ai-predictions'),
        fetch('http://localhost:8001/api/telegram/breaking-news')
      ])

      if (dashboardRes.ok) {
        const data = await dashboardRes.json()
        setNews(data.news || [])
        setSignals(data.signals || [])
        setCrypto(data.crypto || [])
        setSentiment(data.sentiment || [])
        setInsiderTrades(data.insider_trades || [])
        setDailyBrief(data.daily_brief || null)
        setConnected(true)
        setLastUpdate(new Date().toLocaleTimeString())
      }

      if (smartMoneyRes.ok) {
        const smartMoneyData = await smartMoneyRes.json()
        setSmartMoneyNotifications({
          past: smartMoneyData.notifications?.past_filings || [],
          future: smartMoneyData.notifications?.future_expected || []
        })
      }

      if (aiPredictionsRes.ok) {
        const aiData = await aiPredictionsRes.json()
        setAiPredictions(aiData)
      }

      if (telegramRes.ok) {
        const telegramData = await telegramRes.json()
        setTelegramMessages(telegramData.messages || [])
        setTelegramStatus(telegramData.status || null)
      }
    } catch (error) {
      console.error('Failed to fetch data:', error)
      setConnected(false)
    }
  }

  const getPhaseColor = (phase: string): string => {
    switch (phase) {
      case 'DANGER': return '#ff0040'
      case 'EUFORIA': return '#00d9ff'
      case 'ACCUMULATION': return '#d4af37'
      case 'PRE-RUMOR': return '#888888'
      default: return '#00d9ff'
    }
  }

  const getSentimentIcon = (sentiment: string): string => {
    if (sentiment?.includes('bullish')) return '↑'
    if (sentiment?.includes('bearish')) return '↓'
    return '•'
  }

  const getSentimentTone = (interpretation: string): 'success' | 'electric' | 'warning' | 'danger' => {
    const s = interpretation?.toLowerCase() || ''
    if (s.includes('extreme greed') || s.includes('very bullish')) return 'success'
    if (s.includes('greed') || s.includes('bullish')) return 'success'
    if (s.includes('extreme fear') || s.includes('very bearish')) return 'danger'
    if (s.includes('fear') || s.includes('bearish')) return 'warning'
    return 'electric'
  }

  const getSentimentPct = (indicator: SentimentIndicator): number => {
    const scaleMax = indicator.indicator_name === 'VIX' ? 40 : 100
    return Math.max(4, Math.min(100, (indicator.value / scaleMax) * 100))
  }

  const recentNews = news.slice(0, 30)

  return (
    <div className="intelligence-terminal">
      <aside className="terminal-sidebar">
        <div className="terminal-brand">
          <div className="brand-logo">AEON</div>
          <div className="brand-sub">INTELLIGENCE</div>
        </div>

        <nav className="terminal-nav">
          <div className="nav-group-label">Today</div>
          <button
            className={view === 'overview' ? 'active' : ''}
            onClick={() => setView('overview')}
          >
            <span className="nav-glyph">◆</span>
            <span>OVERVIEW</span>
          </button>
          <button
            className={view === 'brief' ? 'active' : ''}
            onClick={() => setView('brief')}
          >
            <span className="nav-glyph">◈</span>
            <span>DAILY BRIEF</span>
          </button>
          <button
            className={view === 'ai-predictions' ? 'active' : ''}
            onClick={() => setView('ai-predictions')}
          >
            <span className="nav-glyph">◉</span>
            <span>AI PREDICTIONS</span>
          </button>

          <div className="nav-group-label">Signals</div>
          <button
            className={view === 'insider' ? 'active' : ''}
            onClick={() => setView('insider')}
          >
            <span className="nav-glyph">◎</span>
            <span>INSIDER TRADING</span>
          </button>
          <button
            className={view === 'telegram' ? 'active' : ''}
            onClick={() => setView('telegram')}
          >
            <span className="nav-glyph">◆</span>
            <span>TELEGRAM FEED</span>
          </button>
          <button
            className={view === 'signals' ? 'active' : ''}
            onClick={() => setView('signals')}
          >
            <span className="nav-glyph">◈</span>
            <span>SIGNALS</span>
          </button>
          <button
            className={view === 'live' ? 'active' : ''}
            onClick={() => setView('live')}
          >
            <span className="nav-glyph">◉</span>
            <span>LIVE FEED</span>
          </button>
        </nav>

        <div className="terminal-status">
          <div className={`status-dot ${connected ? 'active' : ''}`}></div>
          <div className="status-text">
            <div>{connected ? 'CONNECTED' : 'OFFLINE'}</div>
            {connected && <div className="status-time">{lastUpdate}</div>}
          </div>
        </div>
      </aside>

      <main className="terminal-main">
        {view === 'overview' && (
          <div className="terminal-view">
            <div className="view-header">
              <h1>MARKET INTELLIGENCE</h1>
            </div>

            <section className="data-block">
              <div className="block-header">
                <h2>TRADING SIGNALS</h2>
                <p>Real opportunities from insider filings, tagged news, sentiment extremes, and crypto momentum.</p>
              </div>
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>TICKER</th>
                    <th>SIGNAL</th>
                    <th>PHASE</th>
                    <th>ENTRY</th>
                    <th>TARGET</th>
                    <th>STOP</th>
                    <th>CONFIDENCE</th>
                    <th>REASONING</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map(signal => (
                    <tr key={signal.id}>
                      <td className="cell-tickers">{signal.ticker}</td>
                      <td className="cell-type">{signal.signal_type.toUpperCase()}</td>
                      <td className="cell-phase">
                        <span style={{ color: getPhaseColor(signal.phase) }}>{signal.phase}</span>
                      </td>
                      <td className="cell-impact">{signal.entry_price != null ? `$${signal.entry_price.toFixed(2)}` : '—'}</td>
                      <td className="cell-impact" style={{ color: '#00ff88' }}>{signal.target_price != null ? `$${signal.target_price.toFixed(2)}` : '—'}</td>
                      <td className="cell-impact" style={{ color: '#ff0040' }}>{signal.stop_loss != null ? `$${signal.stop_loss.toFixed(2)}` : '—'}</td>
                      <td className="cell-countdown">{signal.confidence}%</td>
                      <td className="cell-rec">{signal.reasoning}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>MARKET SENTIMENT</h2>
                <p>Real-time sentiment indicators from multiple sources.</p>
              </div>
              <div className="sentiment-grid">
                {sentiment.map(ind => {
                  const tone = getSentimentTone(ind.interpretation)
                  return (
                    <div className="sentiment-card" key={ind.id}>
                      <div className="sentiment-card-head">
                        <span className="sentiment-name">{ind.indicator_name}</span>
                        <span className={`sentiment-value tone-${tone}`}>{ind.value.toFixed(1)}</span>
                      </div>
                      <div className="sentiment-bar-track">
                        <div
                          className={`sentiment-bar-fill tone-${tone}`}
                          style={{ width: `${getSentimentPct(ind)}%` }}
                        />
                      </div>
                      <span className={`sentiment-pill tone-${tone}`}>{ind.interpretation}</span>
                      <div className="sentiment-meta">
                        <span>{ind.source}</span>
                        <span>{ind.affected_markets}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>RECENT MARKET UPDATES</h2>
                <p>Latest news and developments. Auto-refreshes every 10 seconds.</p>
              </div>
              <table className="data-grid news-grid">
                <thead>
                  <tr>
                    <th>TIME</th>
                    <th>SOURCE</th>
                    <th>TITLE</th>
                    <th>SENTIMENT</th>
                    <th>TICKERS</th>
                  </tr>
                </thead>
                <tbody>
                  {recentNews.slice(0, 12).map(item => (
                    <tr key={item.id} className={item.urgency === 'breaking' ? 'urgency-breaking' : ''}>
                      <td className="cell-time">{new Date(item.published_at).toLocaleString()}</td>
                      <td className="cell-source">{item.source}</td>
                      <td className="cell-news">{item.title}</td>
                      <td className="cell-sentiment">{getSentimentIcon(item.sentiment)} {item.sentiment}</td>
                      <td className="cell-tickers">{item.tickers}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        )}

        {view === 'live' && (
          <div className="terminal-view">
            <div className="view-header">
              <h1>LIVE NEWS FEED</h1>
              <p>Real-time market updates from multiple sources</p>
            </div>

            <section className="data-block">
              <div className="block-header">
                <h2>ALL UPDATES</h2>
                <p>Chronological feed of market-moving news</p>
              </div>
              <table className="data-grid news-grid">
                <thead>
                  <tr>
                    <th>TIMESTAMP</th>
                    <th>SOURCE</th>
                    <th>TITLE</th>
                    <th>SUMMARY</th>
                    <th>SENTIMENT</th>
                    <th>URGENCY</th>
                    <th>TICKERS</th>
                  </tr>
                </thead>
                <tbody>
                  {recentNews.map(item => (
                    <tr key={item.id} className={item.urgency === 'breaking' ? 'urgency-breaking' : ''}>
                      <td className="cell-time">{new Date(item.published_at).toLocaleString()}</td>
                      <td className="cell-source">{item.source}</td>
                      <td className="cell-news">{item.title}</td>
                      <td className="cell-summary">{item.summary}</td>
                      <td className="cell-sentiment">{getSentimentIcon(item.sentiment)} {item.sentiment}</td>
                      <td className="cell-type">{item.urgency?.toUpperCase() || 'MEDIUM'}</td>
                      <td className="cell-tickers">{item.tickers}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        )}

        {view === 'signals' && (
          <div className="terminal-view">
            <div className="view-header">
              <h1>TRADING SIGNALS</h1>
              <p>Real opportunities detected from market context - insider filings, news, sentiment, and crypto momentum</p>
            </div>

            <section className="data-block">
              <div className="block-header">
                <h2>ACTIVE SIGNALS</h2>
                <p>Real opportunities detected from insider filings, tagged news, sentiment extremes, and crypto momentum</p>
              </div>
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>TICKER</th>
                    <th>SIGNAL</th>
                    <th>PHASE</th>
                    <th>ENTRY PRICE</th>
                    <th>TARGET PRICE</th>
                    <th>STOP LOSS</th>
                    <th>RISK/REWARD</th>
                    <th>CONFIDENCE</th>
                    <th>REASONING</th>
                  </tr>
                </thead>
                <tbody>
                  {signals.map(signal => {
                    const hasFullPrices = signal.entry_price != null && signal.target_price != null && signal.stop_loss != null
                    const risk = hasFullPrices ? signal.entry_price - signal.stop_loss : null
                    const reward = hasFullPrices ? signal.target_price - signal.entry_price : null
                    const rr = risk ? (reward! / risk).toFixed(2) : null

                    return (
                      <tr key={signal.id}>
                        <td className="cell-tickers">{signal.ticker}</td>
                        <td className="cell-type">{signal.signal_type.toUpperCase()}</td>
                        <td className="cell-phase">
                          <span style={{ color: getPhaseColor(signal.phase) }}>{signal.phase}</span>
                        </td>
                        <td className="cell-impact">{signal.entry_price != null ? `$${signal.entry_price.toFixed(2)}` : '—'}</td>
                        <td className="cell-impact" style={{ color: '#00ff88' }}>{signal.target_price != null ? `$${signal.target_price.toFixed(2)}` : '—'}</td>
                        <td className="cell-impact" style={{ color: '#ff0040' }}>{signal.stop_loss != null ? `$${signal.stop_loss.toFixed(2)}` : '—'}</td>
                        <td className="cell-countdown">{rr ? `${rr}:1` : '—'}</td>
                        <td className="cell-countdown">{signal.confidence}%</td>
                        <td className="cell-rec">{signal.reasoning}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </section>
          </div>
        )}

        {view === 'insider' && (
          <div className="terminal-view">
            <div className="view-header">
              <h1>INSIDER TRADING</h1>
              <p>Track what corporate insiders are doing with their own money - the ultimate conviction signal. Real-time SEC Form 4 filings reveal when executives buy or sell their own stock.</p>
              <div className="header-metrics">
                <div className="metric">
                  <span className="metric-value">{insiderTrades.filter(t => t.transaction_type === 'BUY').length}</span>
                  <span className="metric-label">INSIDER BUYS</span>
                </div>
                <div className="metric">
                  <span className="metric-value">{insiderTrades.filter(t => t.significance === 'EXTREME' || t.significance === 'HIGH').length}</span>
                  <span className="metric-label">HIGH SIGNIFICANCE</span>
                </div>
                <div className="metric">
                  <span className="metric-value">
                    ${(insiderTrades.reduce((sum, t) => sum + t.total_value, 0) / 1000000).toFixed(1)}M
                  </span>
                  <span className="metric-label">TOTAL VALUE</span>
                </div>
              </div>
            </div>

            <div className="info-block" style={{ marginBottom: '30px', borderLeftColor: '#d4af37' }}>
              <h3>WHY INSIDER TRADING MATTERS</h3>
              <ul>
                <li><strong>Information Asymmetry:</strong> Corporate insiders (CEOs, CFOs, Board Members) have access to material non-public information about their company's future prospects, product pipelines, and financial health</li>
                <li><strong>Skin in the Game:</strong> When executives buy their own stock with personal money, it's the strongest conviction signal - they're betting their wealth on the company's success</li>
                <li><strong>Leading Indicator:</strong> Insider buying often precedes major positive catalysts (earnings beats, product launches, M&A) by weeks or months. They know what's coming before the market does.</li>
                <li><strong>Market Impact:</strong> Cluster buying by multiple insiders can signal imminent upside. Selling is less reliable (tax planning, diversification) but extreme selling can flag concerns.</li>
                <li><strong>Legal but Powerful:</strong> Insiders must file Form 4 with SEC within 2 business days of transaction. This is public data but most investors ignore it - that's your edge.</li>
              </ul>
            </div>

            <section className="data-block">
              <div className="block-header">
                <h2>🎯 EXTREME SIGNIFICANCE TRADES</h2>
                <p>Highest conviction insider trades - CEOs buying aggressively or making unusually large transactions</p>
              </div>
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>TICKER</th>
                    <th>INSIDER</th>
                    <th>ROLE</th>
                    <th>ACTION</th>
                    <th>SHARES</th>
                    <th>PRICE</th>
                    <th>TOTAL VALUE</th>
                    <th>OWNERSHIP Δ</th>
                    <th>FILING DATE</th>
                    <th>SMART MONEY SIGNAL</th>
                  </tr>
                </thead>
                <tbody>
                  {insiderTrades.filter(t => t.significance === 'EXTREME').length > 0 ? (
                    insiderTrades.filter(t => t.significance === 'EXTREME').map((trade, idx) => (
                      <tr key={idx}>
                        <td className="cell-tickers" style={{ fontWeight: 700 }}>{trade.ticker}</td>
                        <td className="cell-primary">{trade.insider_name}</td>
                        <td className="cell-type">{trade.role}</td>
                        <td className="cell-phase">
                          <span style={{
                            color: trade.transaction_type === 'BUY' ? '#00ff88' : '#ff0040',
                            fontWeight: 700
                          }}>
                            {trade.transaction_type}
                          </span>
                        </td>
                        <td className="cell-impact" style={{ color: '#00d9ff' }}>
                          {trade.shares.toLocaleString()}
                        </td>
                        <td className="cell-impact">${trade.price.toFixed(2)}</td>
                        <td className="cell-impact" style={{ color: '#d4af37', fontWeight: 700 }}>
                          ${(trade.total_value / 1000000).toFixed(2)}M
                        </td>
                        <td className="cell-phase">
                          <span style={{ color: trade.transaction_type === 'BUY' ? '#00ff88' : '#ffa500' }}>
                            {trade.ownership_change}
                          </span>
                        </td>
                        <td className="cell-date">{trade.filing_date}</td>
                        <td className="cell-rec" style={{ fontWeight: 600 }}>{trade.smart_money_signal}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={10} className="cell-empty">No extreme significance trades in recent filings</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>📈 ALL INSIDER TRADES (LAST 90 DAYS)</h2>
                <p>Complete insider trading activity from SEC Form 4 filings - 3 months of history</p>
              </div>
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>TICKER</th>
                    <th>INSIDER</th>
                    <th>ROLE</th>
                    <th>ACTION</th>
                    <th>SHARES</th>
                    <th>PRICE</th>
                    <th>TOTAL VALUE</th>
                    <th>OWNERSHIP Δ</th>
                    <th>SIGNIFICANCE</th>
                    <th>FILING DATE</th>
                    <th>SMART MONEY SIGNAL</th>
                  </tr>
                </thead>
                <tbody>
                  {insiderTrades.length > 0 ? insiderTrades.map((trade, idx) => (
                    <tr key={idx}>
                      <td className="cell-tickers" style={{ fontWeight: 700 }}>{trade.ticker}</td>
                      <td className="cell-primary">{trade.insider_name}</td>
                      <td className="cell-type">{trade.role}</td>
                      <td className="cell-phase">
                        <span style={{
                          color: trade.transaction_type === 'BUY' ? '#00ff88' : '#ff0040',
                          fontWeight: 700
                        }}>
                          {trade.transaction_type}
                        </span>
                      </td>
                      <td className="cell-impact" style={{ color: '#00d9ff' }}>
                        {trade.shares.toLocaleString()}
                      </td>
                      <td className="cell-impact">${trade.price.toFixed(2)}</td>
                      <td className="cell-impact" style={{ color: '#d4af37' }}>
                        ${(trade.total_value / 1000000).toFixed(2)}M
                      </td>
                      <td className="cell-phase">
                        <span style={{ color: trade.transaction_type === 'BUY' ? '#00ff88' : '#ffa500' }}>
                          {trade.ownership_change}
                        </span>
                      </td>
                      <td className="cell-phase">
                        <span style={{
                          color: trade.significance === 'EXTREME' ? '#ff0040' :
                                 trade.significance === 'HIGH' ? '#ffa500' :
                                 trade.significance === 'MEDIUM' ? '#d4af37' : '#888888'
                        }}>
                          {trade.significance}
                        </span>
                      </td>
                      <td className="cell-date">{trade.filing_date}</td>
                      <td className="cell-rec">{trade.smart_money_signal}</td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={11} className="cell-empty">Loading insider trading data...</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>

            {smartMoneyNotifications.future.length > 0 && (
              <section className="data-block">
                <div className="block-header">
                  <h2>UPCOMING REGULATORY DEADLINES</h2>
                  <p>Real public disclosure dates to watch (e.g. 13F) - not a prediction, just the calendar</p>
                </div>
                <table className="data-grid">
                  <thead>
                    <tr>
                      <th>TYPE</th>
                      <th>TITLE</th>
                      <th>DETAIL</th>
                      <th>DAYS AHEAD</th>
                    </tr>
                  </thead>
                  <tbody>
                    {smartMoneyNotifications.future.map((notification) => (
                      <tr key={notification.id}>
                        <td className="cell-type">{notification.type}</td>
                        <td className="cell-primary">{notification.title}</td>
                        <td className="cell-rec">{notification.message}</td>
                        <td className="cell-date">{notification.days_ahead} days</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>
            )}

            <div className="info-block">
              <h3>HOW TO USE INSIDER TRADING DATA</h3>
              <ul>
                <li><strong>Focus on BUYS, not SELLS:</strong> Insiders sell for many reasons (diversification, taxes, divorce) but they buy for ONE reason - they think the stock is going up</li>
                <li><strong>Cluster Buying:</strong> Multiple insiders buying within the same week is extremely bullish. They're coordinating around knowledge of an upcoming catalyst.</li>
                <li><strong>CEO/CFO Transactions:</strong> C-suite executives have the most complete picture. Weight their transactions 3x more than board members.</li>
                <li><strong>Size Matters:</strong> $1M+ purchases are serious conviction. $5M+ is "all-in" level confidence. Compare transaction size to their existing holdings.</li>
                <li><strong>Timing with Events:</strong> Buying before earnings or product launches is the strongest signal. Cross-reference with calendar events.</li>
                <li><strong>Form 4 Filing Window:</strong> SEC requires filing within 2 business days. Recent filings (0-3 days old) give you the freshest edge before news breaks.</li>
              </ul>
            </div>
          </div>
        )}

        {view === 'telegram' && (
          <div className="terminal-view">
            <div className="view-header">
              <h1>TELEGRAM FEED</h1>
              <p>Real messages from the Tradeul_Breaking_News Telegram channel - a real read-only listener, never posts.</p>
              <div className="header-metrics">
                <div className="metric">
                  <span className="metric-value" style={{ color: telegramStatus?.connected ? '#00ff88' : '#ff0040' }}>
                    {telegramStatus?.connected ? 'LIVE' : 'OFFLINE'}
                  </span>
                  <span className="metric-label">CONNECTION</span>
                </div>
                <div className="metric">
                  <span className="metric-value">{telegramStatus?.history_window_days ?? 30}d</span>
                  <span className="metric-label">HISTORY WINDOW</span>
                </div>
                <div className="metric">
                  <span className="metric-value">{telegramStatus?.message_count ?? telegramMessages.length}</span>
                  <span className="metric-label">MESSAGES IN WINDOW</span>
                </div>
              </div>
            </div>

            <div className="info-block" style={{ marginBottom: '30px', borderLeftColor: telegramStatus?.connected ? '#00ff88' : '#ff0040' }}>
              <h3>STATUS</h3>
              <ul>
                <li><strong>Authorized:</strong> {telegramStatus?.authorized === true ? 'yes' : telegramStatus?.authorized === false ? 'no - session expired, needs re-login' : 'unknown'}</li>
                <li><strong>Backfilled on connect:</strong> {telegramStatus?.backfilled_count ?? '...'} real historical messages from the last {telegramStatus?.history_window_days ?? 30} days</li>
                {telegramStatus?.last_error && <li><strong>Last error:</strong> {telegramStatus.last_error}</li>}
                <li>This is a low-frequency channel - an empty table below means the channel genuinely hasn't posted in the window, not that the connection is broken.</li>
              </ul>
            </div>

            <section className="data-block">
              <div className="block-header">
                <h2>MESSAGES ({telegramMessages.length})</h2>
                <p>Newest first, real backfilled history + anything arriving live</p>
              </div>
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>TIME</th>
                    <th>MESSAGE</th>
                    <th>TICKERS</th>
                    <th>SENTIMENT</th>
                  </tr>
                </thead>
                <tbody>
                  {telegramMessages.length > 0 ? telegramMessages.map((msg, idx) => (
                    <tr key={idx}>
                      <td className="cell-date">{new Date(msg.published_at).toLocaleString()}</td>
                      <td className="cell-primary">{msg.summary || msg.title}</td>
                      <td className="cell-tickers">{msg.tickers || '-'}</td>
                      <td className="cell-phase">
                        <span style={{
                          color: msg.sentiment === 'bullish' ? '#00ff88' :
                                 msg.sentiment === 'bearish' ? '#ff0040' : '#d4af37'
                        }}>
                          {msg.sentiment}
                        </span>
                      </td>
                    </tr>
                  )) : (
                    <tr>
                      <td colSpan={4} className="cell-empty">No messages in the last {telegramStatus?.history_window_days ?? 30} days</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </section>
          </div>
        )}

        {view === 'brief' && dailyBrief && (
          <div className="terminal-view">
            <div className="view-header">
              <h1>DAILY INTELLIGENCE BRIEF</h1>
              <p>AI-powered stock recommendations synthesizing all 40+ data sources with full market context</p>
              <div className="brief-meta">
                <span><strong>Date:</strong> {dailyBrief.date}</span>
                <span><strong>Market Regime:</strong> {dailyBrief.market_regime}</span>
                <span><strong>Primary Catalyst:</strong> {dailyBrief.primary_catalyst}</span>
              </div>
            </div>

            {dailyBrief.mega_cap_plays && dailyBrief.mega_cap_plays.length > 0 && (
              <section className="data-block">
                <div className="block-header">
                  <h2>🏛️ MEGA-CAP PLAYS ($500B+)</h2>
                  <p>Market-moving positions with institutional backing and major catalysts</p>
                </div>
                {dailyBrief.mega_cap_plays.map((play, idx) => (
                  <div key={idx} className="recommendation-card accent-gold">
                    <div className="rec-header">
                      <h3>{play.ticker} - {play.action}</h3>
                      <div className="rec-targets">
                        <span className="market-cap">Cap: {play.market_cap}</span>
                        <span className="confidence">Confidence: {play.confidence}</span>
                        <span className="timeframe">Timeframe: {play.timeframe}</span>
                      </div>
                    </div>
                    <div className="rec-body">
                      <p><strong>Catalyst:</strong> {play.catalyst}</p>
                      <p><strong>Smart Money Signal:</strong> {play.smart_money_signal}</p>
                      <p><strong>Technical Setup:</strong> {play.technical_setup}</p>
                      <p><strong>Risk Factor:</strong> {play.risk_factor}</p>
                      <p><strong>Data Sources:</strong> {play.data_sources.join(', ')}</p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            {dailyBrief.large_cap_plays && dailyBrief.large_cap_plays.length > 0 && (
              <section className="data-block">
                <div className="block-header">
                  <h2>🏢 LARGE-CAP PLAYS ($10B-$500B)</h2>
                  <p>Strong conviction plays with institutional flow and technical momentum</p>
                </div>
                {dailyBrief.large_cap_plays.map((play, idx) => (
                  <div key={idx} className="recommendation-card accent-info">
                    <div className="rec-header">
                      <h3>{play.ticker} - {play.action}</h3>
                      <div className="rec-targets">
                        <span className="market-cap">Cap: {play.market_cap}</span>
                        <span className="confidence">Confidence: {play.confidence}</span>
                        <span className="timeframe">Timeframe: {play.timeframe}</span>
                      </div>
                    </div>
                    <div className="rec-body">
                      <p><strong>Catalyst:</strong> {play.catalyst}</p>
                      <p><strong>Smart Money Signal:</strong> {play.smart_money_signal}</p>
                      <p><strong>Technical Setup:</strong> {play.technical_setup}</p>
                      <p><strong>Risk Factor:</strong> {play.risk_factor}</p>
                      <p><strong>Data Sources:</strong> {play.data_sources.join(', ')}</p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            {dailyBrief.mid_cap_opportunities && dailyBrief.mid_cap_opportunities.length > 0 && (
              <section className="data-block">
                <div className="block-header">
                  <h2>🎯 MID-CAP OPPORTUNITIES ($2B-$10B)</h2>
                  <p>High-growth opportunities with strong insider activity and momentum</p>
                </div>
                {dailyBrief.mid_cap_opportunities.map((play, idx) => (
                  <div key={idx} className="recommendation-card accent-success">
                    <div className="rec-header">
                      <h3>{play.ticker} - {play.action}</h3>
                      <div className="rec-targets">
                        <span className="market-cap">Cap: {play.market_cap}</span>
                        <span className="confidence">Confidence: {play.confidence}</span>
                        <span className="timeframe">Timeframe: {play.timeframe}</span>
                      </div>
                    </div>
                    <div className="rec-body">
                      <p><strong>Catalyst:</strong> {play.catalyst}</p>
                      <p><strong>Smart Money Signal:</strong> {play.smart_money_signal}</p>
                      <p><strong>Technical Setup:</strong> {play.technical_setup}</p>
                      <p><strong>Risk Factor:</strong> {play.risk_factor}</p>
                      <p><strong>Data Sources:</strong> {play.data_sources.join(', ')}</p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            {dailyBrief.event_driven_plays && dailyBrief.event_driven_plays.length > 0 && (
              <section className="data-block">
                <div className="block-header">
                  <h2>⚡ EVENT-DRIVEN PLAYS</h2>
                  <p>Time-sensitive opportunities driven by specific catalysts and market events</p>
                </div>
                {dailyBrief.event_driven_plays.map((play, idx) => (
                  <div key={idx} className="recommendation-card accent-warning">
                    <div className="rec-header">
                      <h3>{play.ticker} - {play.action}</h3>
                      <div className="rec-targets">
                        <span className="market-cap">Cap: {play.market_cap}</span>
                        <span className="confidence">Confidence: {play.confidence}</span>
                        <span className="timeframe">Timeframe: {play.timeframe}</span>
                      </div>
                    </div>
                    <div className="rec-body">
                      <p><strong>Catalyst:</strong> {play.catalyst}</p>
                      <p><strong>Smart Money Signal:</strong> {play.smart_money_signal}</p>
                      <p><strong>Technical Setup:</strong> {play.technical_setup}</p>
                      <p><strong>Risk Factor:</strong> {play.risk_factor}</p>
                      <p><strong>Data Sources:</strong> {play.data_sources.join(', ')}</p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            {dailyBrief.sector_plays && dailyBrief.sector_plays.length > 0 && (
              <section className="data-block">
                <div className="block-header">
                  <h2>🔄 SECTOR ROTATION PLAYS</h2>
                  <p>Strategic sector positioning based on macro trends and institutional flows</p>
                </div>
                {dailyBrief.sector_plays.map((play, idx) => (
                  <div key={idx} className="recommendation-card accent-purple">
                    <div className="rec-header">
                      <h3>{play.ticker} - {play.action}</h3>
                      <div className="rec-targets">
                        <span className="market-cap">Cap: {play.market_cap}</span>
                        <span className="sector">Sector: {play.sector}</span>
                        <span className="confidence">Confidence: {play.confidence}</span>
                        <span className="timeframe">Timeframe: {play.timeframe}</span>
                      </div>
                    </div>
                    <div className="rec-body">
                      <p><strong>Catalyst:</strong> {play.catalyst}</p>
                      <p><strong>Smart Money Signal:</strong> {play.smart_money_signal}</p>
                      <p><strong>Technical Setup:</strong> {play.technical_setup}</p>
                      <p><strong>Risk Factor:</strong> {play.risk_factor}</p>
                      <p><strong>Data Sources:</strong> {play.data_sources.join(', ')}</p>
                    </div>
                  </div>
                ))}
              </section>
            )}

            <section className="data-block">
              <div className="block-header">
                <h2>MARKET CONTEXT</h2>
              </div>
              <div className="context-grid">
                <div className="context-item">
                  <h4>KEY EVENTS TODAY</h4>
                  <ul>
                    {dailyBrief.market_context.key_events_today.map((event, idx) => (
                      <li key={idx}>{event}</li>
                    ))}
                  </ul>
                </div>
                <div className="context-item">
                  <h4>MACRO REGIME</h4>
                  <p>{dailyBrief.market_context.macro_regime}</p>
                </div>
                <div className="context-item">
                  <h4>SECTOR ROTATION</h4>
                  <p>{dailyBrief.market_context.sector_rotation}</p>
                </div>
                <div className="context-item">
                  <h4>VOLATILITY SETUP</h4>
                  <p>{dailyBrief.market_context.volatility_setup}</p>
                </div>
                <div className="context-item">
                  <h4>SENTIMENT</h4>
                  <p>{dailyBrief.market_context.sentiment}</p>
                </div>
              </div>
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>ACTION PLAN</h2>
              </div>
              <div className="action-grid">
                <div className="action-column">
                  <h4>IMMEDIATE (TODAY)</h4>
                  <ul>
                    {dailyBrief.action_plan.immediate.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ul>
                </div>
                <div className="action-column">
                  <h4>THIS WEEK</h4>
                  <ul>
                    {dailyBrief.action_plan.this_week.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ul>
                </div>
                <div className="action-column">
                  <h4>THIS MONTH</h4>
                  <ul>
                    {dailyBrief.action_plan.this_month.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>
          </div>
        )}

        {view === 'ai-predictions' && aiPredictions && (
          <div className="terminal-view">
            <div className="view-header">
              <h1>🧠 AI PREDICTION ENGINE</h1>
              <p>Advanced market prediction system using ensemble methods, pattern recognition, and causal reasoning</p>
              <div className="brief-meta">
                <span><strong>Model:</strong> {aiPredictions.meta.model_version}</span>
                <span><strong>Data Sources:</strong> {aiPredictions.meta.total_data_sources}</span>
                <span><strong>Horizon:</strong> {aiPredictions.meta.prediction_horizon}</span>
                <span><strong>Calibration:</strong> {aiPredictions.meta.confidence_calibration}</span>
              </div>
            </div>

            {aiPredictions.prediction_accuracy_stats && (
              <section className="data-block accent-panel-success">
                <div className="block-header">
                  <h2>📊 MODEL ACCURACY STATS</h2>
                  <p>Live-prediction track record, backed by a real historical backtest of the underlying signal</p>
                </div>
                <div className="context-grid">
                  <div className="context-item">
                    <h4>LIVE PREDICTIONS - LAST 30 DAYS</h4>
                    <p><strong>Predictions Made:</strong> {aiPredictions.prediction_accuracy_stats.last_30_days.predictions_made}</p>
                    <p><strong>Resolved:</strong> {aiPredictions.prediction_accuracy_stats.last_30_days.predictions_resolved}</p>
                    <p><strong>Correct:</strong> {aiPredictions.prediction_accuracy_stats.last_30_days.correct}</p>
                    <p className="text-success stat-big"><strong>Accuracy: {(aiPredictions.prediction_accuracy_stats.last_30_days.accuracy * 100).toFixed(1)}%</strong></p>
                    <p><strong>Calibration Score:</strong> {(aiPredictions.prediction_accuracy_stats.last_30_days.calibration_score * 100).toFixed(1)}%</p>
                  </div>
                  <div className="context-item">
                    <h4>BY CATEGORY (real historical backtest)</h4>
                    {Object.entries(aiPredictions.prediction_accuracy_stats.by_category).length === 0 ? (
                      <p className="text-muted">Backtest not computed yet - check back shortly.</p>
                    ) : Object.entries(aiPredictions.prediction_accuracy_stats.by_category).map(([cat, stats]: [string, any]) => (
                      <p key={cat}><strong>{cat}:</strong> {(stats.accuracy * 100).toFixed(1)}% positive (n={stats.n})</p>
                    ))}
                  </div>
                  <div className="context-item">
                    <h4>NOTES</h4>
                    <ul>
                      {aiPredictions.prediction_accuracy_stats.model_improvements.map((imp, idx) => (
                        <li key={idx}>{imp}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {aiPredictions.historical_backtest?.signals ? (
                  <div className="context-grid">
                    <div className="context-item">
                      <h4>BACKTEST METHODOLOGY</h4>
                      <p>{aiPredictions.historical_backtest.methodology}</p>
                      <p>
                        <strong>Period:</strong> {aiPredictions.historical_backtest.period?.start} to{' '}
                        {aiPredictions.historical_backtest.period?.end} ({aiPredictions.historical_backtest.period?.days} days) &nbsp;|&nbsp;
                        <strong> Universe:</strong> {aiPredictions.historical_backtest.universe?.join(', ')} &nbsp;|&nbsp;
                        <strong> Filings checked:</strong> {aiPredictions.historical_backtest.filings_checked}
                      </p>
                    </div>
                    {Object.entries(aiPredictions.historical_backtest.signals).map(([sigName, sig]: [string, any]) => (
                      <div className="context-item" key={sigName}>
                        <h4>{sigName.toUpperCase().replace('_', ' ')} ({sig.events_found} real events found)</h4>
                        {sig.events_found === 0 ? (
                          <p>No real occurrences of this signal in the backtest window.</p>
                        ) : (
                          <table className="mini-table">
                            <thead>
                              <tr><th>Horizon</th><th>Tested</th><th>% Positive</th><th>Avg Return</th></tr>
                            </thead>
                            <tbody>
                              {Object.entries(sig.by_horizon).map(([h, stats]: [string, any]) => (
                                <tr key={h}>
                                  <td>{h}</td>
                                  <td>{stats.signals_tested}</td>
                                  <td>{stats.pct_positive != null ? `${stats.pct_positive}%` : '—'}</td>
                                  <td>{stats.avg_return_pct != null ? `${stats.avg_return_pct}%` : '—'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    ))}
                    <div className="context-item">
                      <h4>CAVEAT</h4>
                      <p>{aiPredictions.historical_backtest.caveat}</p>
                      <p className="text-muted">Sources: {aiPredictions.historical_backtest.data_sources}</p>
                    </div>
                  </div>
                ) : aiPredictions.historical_backtest?.note ? (
                  <p className="text-muted">{aiPredictions.historical_backtest.note}</p>
                ) : null}
              </section>
            )}

            <section className="data-block">
              <div className="block-header">
                <h2>⚡ HIGH-CONFIDENCE PREDICTIONS</h2>
                <p>Strong signal convergence - multiple data sources confirm these predictions</p>
              </div>
              {aiPredictions.high_confidence_predictions.map((pred) => (
                <div key={pred.prediction_id} className="recommendation-card accent-success">
                  <div className="rec-header">
                    <h3>{pred.ticker} - {pred.type}</h3>
                    <div className="rec-targets">
                      <span className="confidence tone-success">
                        Confidence: {(pred.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="timeframe">{pred.timeframe}</span>
                      <span className="action-tag">{pred.action}</span>
                    </div>
                  </div>
                  <div className="rec-body">
                    <p><strong>Prediction:</strong> {pred.prediction}</p>
                    <p><strong>Reasoning:</strong> {pred.reasoning}</p>
                    {pred.supporting_signals && pred.supporting_signals.length > 0 && (
                      <div>
                        <strong>Supporting Signals:</strong>
                        <ul>
                          {pred.supporting_signals.map((signal, idx) => (
                            <li key={idx}>{signal}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {pred.predicted_outcome && (
                      <div className="outcome-box">
                        <strong>Expected Outcomes:</strong>
                        <p className="text-success"><strong>If Correct:</strong> {pred.predicted_outcome.if_correct}</p>
                        <p className="text-danger"><strong>If Wrong:</strong> {pred.predicted_outcome.if_wrong}</p>
                        {pred.predicted_outcome.expected_value && (
                          <p className="text-warning"><strong>Expected Value:</strong> {pred.predicted_outcome.expected_value}</p>
                        )}
                      </div>
                    )}
                    {pred.adversarial_test && (
                      <p className="text-orange" style={{ marginTop: '10px' }}><strong>Adversarial Test:</strong> {pred.adversarial_test}</p>
                    )}
                  </div>
                </div>
              ))}
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>🔍 PATTERN-BASED PREDICTIONS</h2>
                <p>Historical pattern recognition with proven track records</p>
              </div>
              {aiPredictions.pattern_based_predictions.map((pred) => (
                <div key={pred.prediction_id} className="recommendation-card accent-info">
                  <div className="rec-header">
                    <h3>{pred.ticker} - {pred.pattern_type}</h3>
                    <div className="rec-targets">
                      <span className="confidence tone-info">
                        Confidence: {(pred.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="action-tag">{pred.action}</span>
                    </div>
                  </div>
                  <div className="rec-body">
                    <p><strong>Prediction:</strong> {pred.prediction}</p>
                    <p><strong>Historical Precedent:</strong> {pred.historical_precedent}</p>
                    {pred.supporting_data && pred.supporting_data.length > 0 && (
                      <div>
                        <strong>Supporting Data:</strong>
                        <ul>
                          {pred.supporting_data.map((data, idx) => (
                            <li key={idx}>{data}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {pred.predicted_move && (
                      <p className="text-success"><strong>Predicted Move:</strong> {pred.predicted_move}</p>
                    )}
                  </div>
                </div>
              ))}
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>🔗 CAUSAL CHAIN PREDICTIONS</h2>
                <p>Event-driven predictions based on causal reasoning (A causes B causes C)</p>
              </div>
              {aiPredictions.causal_predictions.map((pred) => (
                <div key={pred.prediction_id} className="recommendation-card accent-orange">
                  <div className="rec-header">
                    <h3>Causal Chain Analysis</h3>
                    <div className="rec-targets">
                      <span className="confidence tone-orange">
                        Confidence: {(pred.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="action-tag">{pred.action}</span>
                    </div>
                  </div>
                  <div className="rec-body">
                    <p className="text-orange"><strong>Causal Chain:</strong> {pred.causal_chain}</p>
                    <p><strong>Prediction:</strong> {pred.prediction}</p>
                    <p><strong>Reasoning:</strong> {pred.reasoning}</p>
                    {pred.supporting_data && pred.supporting_data.length > 0 && (
                      <div>
                        <strong>Supporting Data:</strong>
                        <ul>
                          {pred.supporting_data.map((data, idx) => (
                            <li key={idx}>{data}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {pred.predicted_outcome && (
                      <p className="text-success"><strong>Predicted Outcome:</strong> {pred.predicted_outcome}</p>
                    )}
                  </div>
                </div>
              ))}
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>🔄 CONTRARIAN PREDICTIONS</h2>
                <p>Against-consensus predictions when market sentiment is wrong</p>
              </div>
              {aiPredictions.contrarian_predictions.map((pred) => (
                <div key={pred.prediction_id} className="recommendation-card accent-purple">
                  <div className="rec-header">
                    <h3>Contrarian View</h3>
                    <div className="rec-targets">
                      <span className="confidence tone-purple">
                        Confidence: {(pred.confidence * 100).toFixed(0)}%
                      </span>
                      <span className="action-tag">{pred.action}</span>
                    </div>
                  </div>
                  <div className="rec-body">
                    <p className="text-purple"><strong>Contrarian View:</strong> {pred.contrarian_view}</p>
                    <p><strong>Prediction:</strong> {pred.prediction}</p>
                    <p><strong>Reasoning:</strong> {pred.reasoning}</p>
                    {pred.supporting_data && pred.supporting_data.length > 0 && (
                      <div>
                        <strong>Supporting Data:</strong>
                        <ul>
                          {pred.supporting_data.map((data, idx) => (
                            <li key={idx}>{data}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {pred.predicted_outcome && (
                      <p className="text-orange"><strong>Predicted Outcome:</strong> {pred.predicted_outcome}</p>
                    )}
                  </div>
                </div>
              ))}
            </section>

            <section className="data-block">
              <div className="block-header">
                <h2>⚠️ BLACK SWAN MONITORS</h2>
                <p>Tail risk monitoring - low probability, high impact scenarios</p>
              </div>
              {aiPredictions.black_swan_monitors.map((risk) => (
                <div key={risk.risk_id} className="recommendation-card accent-danger">
                  <div className="rec-header">
                    <h3>{risk.risk_type} Risk</h3>
                    <div className="rec-targets">
                      <span className="text-danger stat-big">
                        Probability: {(risk.probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="rec-body">
                    <p><strong>Scenario:</strong> {risk.scenario}</p>
                    <p className="text-danger"><strong>Impact If Occurs:</strong> {risk.impact_if_occurs}</p>
                    {risk.early_warning_indicators && risk.early_warning_indicators.length > 0 && (
                      <div>
                        <strong>Early Warning Indicators:</strong>
                        <ul>
                          {risk.early_warning_indicators.map((indicator, idx) => (
                            <li key={idx}>{indicator}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {risk.hedge && (
                      <p className="text-success"><strong>Hedge Strategy:</strong> {risk.hedge}</p>
                    )}
                  </div>
                </div>
              ))}
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default Intelligence
