import { useState, useEffect } from 'react';
import './Intelligence.css';
import TickerLens from './TickerLens';
import AlphaView from './AlphaView';
import { formatEventDate, timeAgo } from './format';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8003';

interface NewsItem {
    id: number;
    title: string;
    published_at: string;
    source: string;
    sentiment: string;
    summary: string;
    url: string;
    tickers: string;
    urgency?: string;
}

interface TelegramStatus {
    connected: boolean;
    authorized: boolean | null;
    last_error: string | null;
    started_at: string | null;
    history_window_days: number;
    backfilled_count: number | null;
    message_count: number;
}

interface Signal {
    id: number;
    ticker: string;
    signal_type: string;
    phase: string;
    entry_price: number | null;
    target_price: number | null;
    stop_loss: number | null;
    confidence: number;
    reasoning: string;
    trigger?: string;
}

interface SentimentIndicator {
    id: number;
    source: string;
    indicator_name: string;
    value: number;
    interpretation: string;
    affected_markets: string;
    timestamp: string;
}

interface InsiderTrade {
    ticker: string;
    insider_name: string;
    role: string;
    transaction_type: string;
    shares: number;
    price: number;
    total_value: number;
    date: string;
    filing_date: string;
    ownership_change: string;
    significance: string;
    smart_money_signal: string;
}

interface SmartMoneyNotification {
    id: number;
    type: string;
    ticker: string;
    title: string;
    message: string;
    significance: string;
    timestamp: string;
    days_ago?: number;
    days_ahead?: number;
    action: string;
    value?: number;
    expected?: boolean;
}

interface DailyBrief {
    date: string;
    market_regime: string;
    primary_catalyst: string;
    mega_cap_plays?: Array<{
        ticker: string;
        market_cap: string;
        action: string;
        target: string;
        stop: string;
        confidence: string;
        timeframe: string;
        rationale: string;
        risks: string;
        catalyst: string;
        smart_money_signal?: string;
        technical_setup?: string;
        risk_factor?: string;
        data_sources: string[];
    }>;
    large_cap_plays?: Array<{
        ticker: string;
        market_cap: string;
        action: string;
        target: string;
        stop: string;
        confidence: string;
        timeframe: string;
        rationale: string;
        risks: string;
        catalyst: string;
        smart_money_signal?: string;
        technical_setup?: string;
        risk_factor?: string;
        data_sources: string[];
    }>;
    mid_cap_opportunities?: Array<{
        ticker: string;
        market_cap: string;
        action: string;
        target: string;
        stop: string;
        confidence: string;
        timeframe: string;
        rationale: string;
        risks: string;
        catalyst: string;
        smart_money_signal?: string;
        technical_setup?: string;
        risk_factor?: string;
        data_sources: string[];
    }>;
    event_driven_plays?: Array<{
        ticker: string;
        market_cap: string;
        action: string;
        target: string;
        stop: string;
        confidence: string;
        timeframe: string;
        rationale: string;
        risks: string;
        catalyst: string;
        smart_money_signal?: string;
        technical_setup?: string;
        risk_factor?: string;
        data_sources: string[];
    }>;
    sector_plays?: Array<{
        sector: string;
        tickers: string[];
        action: string;
        rationale: string;
        catalyst: string;
        confidence?: string;
        timeframe?: string;
        market_cap?: string;
        smart_money_signal?: string;
        technical_setup?: string;
        risk_factor?: string;
        data_sources: string[];
    }>;
    top_recommendations: Array<{
        ticker: string;
        action: string;
        target: string;
        stop: string;
        confidence: string;
        timeframe: string;
        rationale: string;
        risks: string;
        data_sources: string[];
    }>;
    market_context: {
        key_events_today: string[];
        macro_regime: string;
        sector_rotation: string;
        volatility_setup: string;
        sentiment: string;
        news_driven_movers?: string[];
    };
    action_plan: {
        immediate: string[];
        this_week: string[];
        this_month: string[];
    };
    risk_management?: {
        market_risks: string;
        position_sizing: string;
        hedging: string;
        watch_levels: string;
    };
    smart_money_activity?: {
        insider_trades_summary: string;
        congressional_trades: string;
        institutional_flow: string;
        cluster_buying_alerts: string;
    };
    mode?: 'live' | 'rules' | 'demo';
    data_edge?: string;
    demo_note?: string;
}

interface AIPrediction {
    prediction_id: string;
    type?: string;
    ticker?: string;
    sector?: string;
    prediction: string;
    confidence: number;
    timeframe: string;
    supporting_signals?: string[];
    supporting_data?: string[];
    historical_precedent?: string;
    predicted_outcome?: {
        if_correct?: string;
        if_wrong?: string;
        if_approved?: string;
        if_delayed?: string;
        if_rejected?: string;
        if_miss_to_3_2?: string;
        if_inline_3_3?: string;
        if_beat_to_3_4_plus?: string;
        expected_value?: string;
    };
    predicted_move?: string;
    reasoning: string;
    adversarial_test?: string;
    action: string;
    pattern_type?: string;
    causal_chain?: string;
    contrarian_view?: string;
    risk_id?: string;
    risk_type?: string;
    scenario?: string;
    probability?: number;
    impact_if_occurs?: string;
    early_warning_indicators?: string[];
    hedge?: string;
}

interface AIPredictions {
    meta: {
        generated_at: string;
        model_version: string;
        prediction_horizon: string;
        confidence_calibration: string;
        total_data_sources: number;
        training_data: string;
        mode?: 'live' | 'rules' | 'demo';
        note?: string | null;
    };
    high_confidence_predictions: AIPrediction[];
    pattern_based_predictions: AIPrediction[];
    causal_predictions: AIPrediction[];
    contrarian_predictions: AIPrediction[];
    black_swan_monitors: AIPrediction[];
    prediction_accuracy_stats: {
        last_30_days: {
            predictions_made: number;
            predictions_resolved: number;
            correct: number;
            accuracy: number;
            avg_confidence: number;
            calibration_score: number;
        };
        by_category: {
            [key: string]: {
                accuracy: number;
                n: number;
            };
        };
        live_prediction_by_category?: {
            [key: string]: {
                n: number;
                correct: number;
                accuracy: number;
            };
        };
        model_improvements: string[];
    };
    historical_backtest?: {
        status?: string;
        note?: string;
        methodology?: string;
        universe?: string[];
        period?: { start: string; end: string; days: number };
        filings_checked?: number;
        signals?: {
            [key: string]: {
                events_found: number;
                by_horizon: {
                    [horizon: string]: {
                        signals_tested: number;
                        pct_positive: number | null;
                        avg_return_pct: number | null;
                    };
                };
                sample_events: Array<{
                    ticker: string;
                    date: string;
                    insider_or_insiders: string | string[];
                    value: number;
                    returns_by_horizon_pct: { [horizon: string]: number };
                }>;
            };
        };
        data_sources?: string;
        caveat?: string;
        computed_at?: string;
    };
}

interface CalendarEvent {
    id: number;
    title: string;
    description: string;
    date: string;
    event_type: string;
    phase: string;
    affected_tickers: string[];
    recommendation: string;
    impact_score: number;
    days_until: number;
    phase_color: string;
}

interface SourceStatus {
    name: string;
    category?: string;
    status: string;
    success_rate: number | null;
    last_success_at?: string | null;
    last_attempt_at?: string | null;
    last_error?: string | null;
    success_count?: number;
    fail_count?: number;
    connected?: boolean;
    authorized?: boolean | null;
    message_count?: number;
}

interface SourcesStatusResponse {
    sources: SourceStatus[];
    summary: { total_sources: number; active_now: number; avg_success_rate: number };
    last_update: string;
}

interface VolatilityData {
    vix: { value: number | null; bucket: string };
    fear_greed: { value: number; rating: string } | null;
    reddit_sentiment: { value: number; avg_upvote_ratio: number; total_score: number; top_titles: string[] } | null;
    volatility_catalysts: CalendarEvent[];
    last_update: string;
}

interface InsiderTrade90 {
    ticker: string;
    insider_name: string;
    role: string;
    transaction_type: string;
    total_value: number;
    shares: number;
    date: string;
}

interface InsiderTrades90Response {
    trades: InsiderTrade90[];
    summary: {
        window_days: number;
        total_trades: number;
        buys: number;
        sells: number;
        total_buy_value: number;
        total_sell_value: number;
    };
}

type ViewType =
    | 'ticker'
    | 'alpha'
    | 'overview'
    | 'live'
    | 'signals'
    | 'insider'
    | 'telegram'
    | 'brief'
    | 'ai-predictions'
    | 'calendar'
    | 'sources'
    | 'volatility';

function Intelligence() {
    // Aeon Analysis links here as ?ticker=XYZ — open that name's lens directly.
    const initialTicker = (new URLSearchParams(window.location.search).get('ticker') || '').trim().toUpperCase();
    const [view, setView] = useState<ViewType>(initialTicker ? 'ticker' : 'overview');
    const [lensTicker, setLensTicker] = useState<string>(initialTicker);
    const openLens = (t: string) => {
        const tk = t.trim().toUpperCase();
        if (!tk || tk === 'ALL' || tk === 'N/A') return;
        setLensTicker(tk);
        setView('ticker');
        const url = new URL(window.location.href);
        url.searchParams.set('ticker', tk);
        window.history.replaceState(null, '', url);
    };
    const [calendarMode, setCalendarMode] = useState<'list' | 'month'>('list');
    const now0 = new Date();
    const [viewMonth, setViewMonth] = useState<number>(now0.getMonth());
    const [viewYear, setViewYear] = useState<number>(now0.getFullYear());
    const [news, setNews] = useState<NewsItem[]>([]);
    const [signals, setSignals] = useState<Signal[]>([]);
    const [sentiment, setSentiment] = useState<SentimentIndicator[]>([]);
    const [insiderTrades, setInsiderTrades] = useState<InsiderTrade[]>([]);
    const [dailyBrief, setDailyBrief] = useState<DailyBrief | null>(null);
    const [aiPredictions, setAiPredictions] = useState<AIPredictions | null>(null);
    const [smartMoneyNotifications, setSmartMoneyNotifications] = useState<{
        past: SmartMoneyNotification[];
        future: SmartMoneyNotification[];
    }>({ past: [], future: [] });
    const [telegramMessages, setTelegramMessages] = useState<NewsItem[]>([]);
    const [telegramStatus, setTelegramStatus] = useState<TelegramStatus | null>(null);
    const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
    const [sourcesStatus, setSourcesStatus] = useState<SourcesStatusResponse | null>(null);
    const [volatility, setVolatility] = useState<VolatilityData | null>(null);
    const [insiderTrades90, setInsiderTrades90] = useState<InsiderTrades90Response | null>(null);
    const [connected, setConnected] = useState(false);
    const [lastUpdate, setLastUpdate] = useState<string>('');

    // The backend refreshes its caches every few minutes, so polling once a minute is
    // plenty — and skipping polls while the tab is hidden saves everyone's quota.
    useEffect(() => {
        fetchAllData();
        const interval = setInterval(() => {
            if (document.visibilityState === 'visible') fetchAllData();
        }, 60000);
        const onVisible = () => document.visibilityState === 'visible' && fetchAllData();
        document.addEventListener('visibilitychange', onVisible);
        return () => {
            clearInterval(interval);
            document.removeEventListener('visibilitychange', onVisible);
        };
    }, []);

    const fetchAllData = async () => {
        try {
            const [dashboardRes, smartMoneyRes, aiPredictionsRes, telegramRes, calendarRes, sourcesRes, volatilityRes, insider90Res] =
                await Promise.all([
                    fetch(`${API_BASE}/api/dashboard`),
                    fetch(`${API_BASE}/api/smart-money/notifications`),
                    fetch(`${API_BASE}/api/ai-predictions`),
                    fetch(`${API_BASE}/api/telegram/breaking-news?limit=300`),
                    fetch(`${API_BASE}/api/events/live?timeframe=90days`),
                    fetch(`${API_BASE}/api/sources/status`),
                    fetch(`${API_BASE}/api/volatility`),
                    fetch(`${API_BASE}/api/insider-trades?days=90`),
                ]);

            if (dashboardRes.ok) {
                const data = await dashboardRes.json();
                setNews(data.news || []);
                setSignals(data.signals || []);
                setSentiment(data.sentiment || []);
                setInsiderTrades(data.insider_trades || []);
                setDailyBrief(data.daily_brief || null);
                setConnected(true);
                setLastUpdate(new Date().toLocaleTimeString());
            } else {
                setConnected(false);
            }

            if (smartMoneyRes.ok) {
                const smartMoneyData = await smartMoneyRes.json();
                setSmartMoneyNotifications({
                    past: smartMoneyData.notifications?.past_filings || [],
                    future: smartMoneyData.notifications?.future_expected || [],
                });
            }

            if (aiPredictionsRes.ok) {
                const aiData = await aiPredictionsRes.json();
                setAiPredictions(aiData);
            }

            if (telegramRes.ok) {
                const telegramData = await telegramRes.json();
                setTelegramMessages(telegramData.messages || []);
                setTelegramStatus(telegramData.status || null);
            }

            if (calendarRes.ok) {
                const calendarData = await calendarRes.json();
                setCalendarEvents(calendarData.events || []);
            }

            if (sourcesRes.ok) {
                setSourcesStatus(await sourcesRes.json());
            }

            if (volatilityRes.ok) {
                setVolatility(await volatilityRes.json());
            }

            if (insider90Res.ok) {
                setInsiderTrades90(await insider90Res.json());
            }
        } catch (error) {
            console.error('Failed to fetch data:', error);
            setConnected(false);
        }
    };

    const getPhaseColor = (phase: string): string => {
        switch (phase) {
            case 'DANGER':
                return '#ff0040';
            case 'EUFORIA':
                return '#00d9ff';
            case 'ACCUMULATION':
                return '#d4af37';
            case 'PRE-RUMOR':
                return '#888888';
            default:
                return '#00d9ff';
        }
    };

    const getSentimentIcon = (sentiment: string): string => {
        if (sentiment?.includes('bullish')) return '↑';
        if (sentiment?.includes('bearish')) return '↓';
        return '•';
    };

    const getSentimentTone = (interpretation: string): 'success' | 'electric' | 'warning' | 'danger' => {
        const s = interpretation?.toLowerCase() || '';
        if (s.includes('extreme greed') || s.includes('very bullish')) return 'success';
        if (s.includes('greed') || s.includes('bullish')) return 'success';
        if (s.includes('extreme fear') || s.includes('very bearish')) return 'danger';
        if (s.includes('fear') || s.includes('bearish')) return 'warning';
        return 'electric';
    };

    const getSentimentPct = (indicator: SentimentIndicator): number => {
        const scaleMax = indicator.indicator_name === 'VIX' ? 40 : 100;
        return Math.max(4, Math.min(100, (indicator.value / scaleMax) * 100));
    };

    const recentNews = news.slice(0, 30);

    return (
        <div className="intelligence-terminal">
            <aside className="terminal-sidebar">
                <div className="terminal-brand">
                    <div className="brand-logo">AEON</div>
                    <div className="brand-sub">INTELLIGENCE</div>
                </div>

                <nav className="terminal-nav">
                    <form
                        className="lens-search sidebar"
                        onSubmit={(e) => {
                            e.preventDefault();
                            const v = new FormData(e.currentTarget).get('t');
                            if (typeof v === 'string') openLens(v);
                        }}
                    >
                        <input name="t" placeholder="Ticker lens…" aria-label="Open ticker lens" />
                    </form>
                    <div className="nav-group-label">Today</div>
                    <button className={view === 'overview' ? 'active' : ''} onClick={() => setView('overview')}>
                        <span className="nav-glyph">◆</span>
                        <span>OVERVIEW</span>
                    </button>
                    <button className={view === 'alpha' ? 'active' : ''} onClick={() => setView('alpha')}>
                        <span className="nav-glyph">α</span>
                        <span>ALPHA</span>
                    </button>
                    <button className={view === 'ticker' ? 'active' : ''} onClick={() => setView('ticker')}>
                        <span className="nav-glyph">⌖</span>
                        <span>TICKER LENS{lensTicker ? ` · ${lensTicker}` : ''}</span>
                    </button>
                    <button className={view === 'brief' ? 'active' : ''} onClick={() => setView('brief')}>
                        <span className="nav-glyph">◈</span>
                        <span>DAILY BRIEF</span>
                    </button>
                    <button className={view === 'ai-predictions' ? 'active' : ''} onClick={() => setView('ai-predictions')}>
                        <span className="nav-glyph">◉</span>
                        <span>AI PREDICTIONS</span>
                    </button>

                    <div className="nav-group-label">Markets</div>
                    <button className={view === 'calendar' ? 'active' : ''} onClick={() => setView('calendar')}>
                        <span className="nav-glyph">◷</span>
                        <span>CALENDAR</span>
                    </button>
                    <button className={view === 'volatility' ? 'active' : ''} onClick={() => setView('volatility')}>
                        <span className="nav-glyph">▲</span>
                        <span>VOLATILITY</span>
                    </button>

                    <div className="nav-group-label">Signals</div>
                    <button className={view === 'insider' ? 'active' : ''} onClick={() => setView('insider')}>
                        <span className="nav-glyph">◎</span>
                        <span>INSIDER TRADING</span>
                    </button>
                    <button className={view === 'telegram' ? 'active' : ''} onClick={() => setView('telegram')}>
                        <span className="nav-glyph">◆</span>
                        <span>TELEGRAM FEED</span>
                    </button>
                    <button className={view === 'signals' ? 'active' : ''} onClick={() => setView('signals')}>
                        <span className="nav-glyph">◈</span>
                        <span>SIGNALS</span>
                    </button>
                    <button className={view === 'live' ? 'active' : ''} onClick={() => setView('live')}>
                        <span className="nav-glyph">◉</span>
                        <span>LIVE FEED</span>
                    </button>

                    <div className="nav-group-label">System</div>
                    <button className={view === 'sources' ? 'active' : ''} onClick={() => setView('sources')}>
                        <span className="nav-glyph">⛁</span>
                        <span>DATA SOURCES</span>
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
                {view === 'ticker' && <TickerLens apiBase={API_BASE} ticker={lensTicker} onTicker={openLens} />}
                {view === 'alpha' && <AlphaView apiBase={API_BASE} onTicker={openLens} />}
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
                                    {signals.length === 0 && (
                                        <tr>
                                            <td colSpan={8} className="cell-empty">
                                                No active signals. Signals only come from real inputs — insider buys, tagged news, sentiment
                                                extremes — so this stays empty while those sources are quiet or unreachable.
                                            </td>
                                        </tr>
                                    )}
                                    {signals.map((signal) => (
                                        <tr key={signal.id}>
                                            <td className="cell-tickers">
                                                <button className="ticker-link" onClick={() => openLens(signal.ticker)}>
                                                    {signal.ticker}
                                                </button>
                                            </td>
                                            <td className="cell-type">{signal.signal_type.toUpperCase()}</td>
                                            <td className="cell-phase">
                                                <span style={{ color: getPhaseColor(signal.phase) }}>{signal.phase}</span>
                                            </td>
                                            <td className="cell-impact">
                                                {signal.entry_price != null ? `$${signal.entry_price.toFixed(2)}` : '—'}
                                            </td>
                                            <td className="cell-impact" style={{ color: '#00ff88' }}>
                                                {signal.target_price != null ? `$${signal.target_price.toFixed(2)}` : '—'}
                                            </td>
                                            <td className="cell-impact" style={{ color: '#ff0040' }}>
                                                {signal.stop_loss != null ? `$${signal.stop_loss.toFixed(2)}` : '—'}
                                            </td>
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
                                {sentiment.length === 0 && (
                                    <p className="text-muted">
                                        No sentiment readings available — CNN Fear &amp; Greed, Reddit and VIX are all unreachable right
                                        now.
                                    </p>
                                )}
                                {sentiment.map((ind) => {
                                    const tone = getSentimentTone(ind.interpretation);
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
                                    );
                                })}
                            </div>
                        </section>

                        <section className="data-block">
                            <div className="block-header">
                                <h2>RECENT MARKET UPDATES</h2>
                                <p>Latest news and developments. Refreshes every minute.</p>
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
                                    {recentNews.length === 0 && (
                                        <tr>
                                            <td colSpan={5} className="cell-empty">
                                                No headlines right now — the news feeds are unreachable. See Data Sources for details.
                                            </td>
                                        </tr>
                                    )}
                                    {recentNews.slice(0, 12).map((item) => (
                                        <tr key={item.id} className={item.urgency === 'breaking' ? 'urgency-breaking' : ''}>
                                            <td className="cell-time" title={new Date(item.published_at).toLocaleString()}>
                                                {timeAgo(item.published_at)}
                                            </td>
                                            <td className="cell-source">{item.source}</td>
                                            <td className="cell-news">
                                                {item.url ? (
                                                    <a href={item.url} target="_blank" rel="noreferrer">
                                                        {item.title}
                                                    </a>
                                                ) : (
                                                    item.title
                                                )}
                                            </td>
                                            <td className="cell-sentiment">
                                                {getSentimentIcon(item.sentiment)} {item.sentiment}
                                            </td>
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
                                    {recentNews.length === 0 && (
                                        <tr>
                                            <td colSpan={7} className="cell-empty">
                                                No headlines right now — the news feeds are unreachable. See Data Sources for details.
                                            </td>
                                        </tr>
                                    )}
                                    {recentNews.map((item) => (
                                        <tr key={item.id} className={item.urgency === 'breaking' ? 'urgency-breaking' : ''}>
                                            <td className="cell-time" title={new Date(item.published_at).toLocaleString()}>
                                                {timeAgo(item.published_at)}
                                            </td>
                                            <td className="cell-source">{item.source}</td>
                                            <td className="cell-news">
                                                {item.url ? (
                                                    <a href={item.url} target="_blank" rel="noreferrer">
                                                        {item.title}
                                                    </a>
                                                ) : (
                                                    item.title
                                                )}
                                            </td>
                                            <td className="cell-summary">{item.summary}</td>
                                            <td className="cell-sentiment">
                                                {getSentimentIcon(item.sentiment)} {item.sentiment}
                                            </td>
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
                                <p>
                                    Real opportunities detected from insider filings, tagged news, sentiment extremes, and crypto momentum
                                </p>
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
                                    {signals.map((signal) => {
                                        const hasFullPrices =
                                            signal.entry_price != null && signal.target_price != null && signal.stop_loss != null;
                                        const risk = hasFullPrices ? signal.entry_price! - signal.stop_loss! : null;
                                        const reward = hasFullPrices ? signal.target_price! - signal.entry_price! : null;
                                        const rr = risk ? (reward! / risk).toFixed(2) : null;

                                        return (
                                            <tr key={signal.id}>
                                                <td className="cell-tickers">
                                                    <button className="ticker-link" onClick={() => openLens(signal.ticker)}>
                                                        {signal.ticker}
                                                    </button>
                                                </td>
                                                <td className="cell-type">{signal.signal_type.toUpperCase()}</td>
                                                <td className="cell-phase">
                                                    <span style={{ color: getPhaseColor(signal.phase) }}>{signal.phase}</span>
                                                </td>
                                                <td className="cell-impact">
                                                    {signal.entry_price != null ? `$${signal.entry_price.toFixed(2)}` : '—'}
                                                </td>
                                                <td className="cell-impact" style={{ color: '#00ff88' }}>
                                                    {signal.target_price != null ? `$${signal.target_price.toFixed(2)}` : '—'}
                                                </td>
                                                <td className="cell-impact" style={{ color: '#ff0040' }}>
                                                    {signal.stop_loss != null ? `$${signal.stop_loss.toFixed(2)}` : '—'}
                                                </td>
                                                <td className="cell-countdown">{rr ? `${rr}:1` : '—'}</td>
                                                <td className="cell-countdown">{signal.confidence}%</td>
                                                <td className="cell-rec">{signal.reasoning}</td>
                                            </tr>
                                        );
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
                            <p>
                                Track what corporate insiders are doing with their own money - the ultimate conviction signal. Real-time SEC
                                Form 4 filings reveal when executives buy or sell their own stock.
                            </p>
                            <div className="header-metrics">
                                <div className="metric">
                                    <span className="metric-value">
                                        {insiderTrades90
                                            ? insiderTrades90.summary.buys
                                            : insiderTrades.filter((t) => t.transaction_type === 'BUY').length}
                                    </span>
                                    <span className="metric-label">INSIDER BUYS (90D)</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">
                                        {insiderTrades.filter((t) => t.significance === 'EXTREME' || t.significance === 'HIGH').length}
                                    </span>
                                    <span className="metric-label">HIGH SIGNIFICANCE</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">
                                        $
                                        {insiderTrades90
                                            ? (
                                                  (insiderTrades90.summary.total_buy_value + insiderTrades90.summary.total_sell_value) /
                                                  1000000
                                              ).toFixed(1)
                                            : (insiderTrades.reduce((sum, t) => sum + t.total_value, 0) / 1000000).toFixed(1)}
                                        M
                                    </span>
                                    <span className="metric-label">TOTAL VALUE (90D)</span>
                                </div>
                            </div>
                        </div>

                        <div className="info-block" style={{ marginBottom: '30px', borderLeftColor: '#d4af37' }}>
                            <h3>WHY INSIDER TRADING MATTERS</h3>
                            <ul>
                                <li>
                                    <strong>Information Asymmetry:</strong> Corporate insiders (CEOs, CFOs, Board Members) have access to
                                    material non-public information about their company's future prospects, product pipelines, and financial
                                    health
                                </li>
                                <li>
                                    <strong>Skin in the Game:</strong> When executives buy their own stock with personal money, it's the
                                    strongest conviction signal - they're betting their wealth on the company's success
                                </li>
                                <li>
                                    <strong>Leading Indicator:</strong> Insider buying often precedes major positive catalysts (earnings
                                    beats, product launches, M&A) by weeks or months. They know what's coming before the market does.
                                </li>
                                <li>
                                    <strong>Market Impact:</strong> Cluster buying by multiple insiders can signal imminent upside. Selling
                                    is less reliable (tax planning, diversification) but extreme selling can flag concerns.
                                </li>
                                <li>
                                    <strong>Legal but Powerful:</strong> Insiders must file Form 4 with SEC within 2 business days of
                                    transaction. This is public data but most investors ignore it - that's your edge.
                                </li>
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
                                    {insiderTrades.filter((t) => t.significance === 'EXTREME').length > 0 ? (
                                        insiderTrades
                                            .filter((t) => t.significance === 'EXTREME')
                                            .map((trade, idx) => (
                                                <tr key={idx}>
                                                    <td className="cell-tickers" style={{ fontWeight: 700 }}>
                                                        {trade.ticker}
                                                    </td>
                                                    <td className="cell-primary">{trade.insider_name}</td>
                                                    <td className="cell-type">{trade.role}</td>
                                                    <td className="cell-phase">
                                                        <span
                                                            style={{
                                                                color: trade.transaction_type === 'BUY' ? '#00ff88' : '#ff0040',
                                                                fontWeight: 700,
                                                            }}
                                                        >
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
                                                    <td className="cell-rec" style={{ fontWeight: 600 }}>
                                                        {trade.smart_money_signal}
                                                    </td>
                                                </tr>
                                            ))
                                    ) : (
                                        <tr>
                                            <td colSpan={10} className="cell-empty">
                                                No extreme significance trades in recent filings
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </section>

                        <section className="data-block">
                            <div className="block-header">
                                <h2>📈 ALL INSIDER TRADES (LAST 90 DAYS)</h2>
                                <p>
                                    Real, persisted SEC Form 4 activity
                                    {insiderTrades90
                                        ? ` - window: last ${insiderTrades90.summary.window_days} days (${insiderTrades90.summary.total_trades} trades, ${insiderTrades90.summary.buys} buys / ${insiderTrades90.summary.sells} sells)`
                                        : ' - loading 90-day window...'}
                                </p>
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
                                        <th>DATE</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {insiderTrades90 && insiderTrades90.trades.length > 0 ? (
                                        insiderTrades90.trades.map((trade, idx) => (
                                            <tr key={idx}>
                                                <td className="cell-tickers" style={{ fontWeight: 700 }}>
                                                    {trade.ticker}
                                                </td>
                                                <td className="cell-primary">{trade.insider_name}</td>
                                                <td className="cell-type">{trade.role}</td>
                                                <td className="cell-phase">
                                                    <span
                                                        style={{
                                                            color: trade.transaction_type === 'BUY' ? '#00ff88' : '#ff0040',
                                                            fontWeight: 700,
                                                        }}
                                                    >
                                                        {trade.transaction_type}
                                                    </span>
                                                </td>
                                                <td className="cell-impact" style={{ color: '#00d9ff' }}>
                                                    {trade.shares.toLocaleString()}
                                                </td>
                                                <td className="cell-impact">
                                                    ${trade.shares ? (trade.total_value / trade.shares).toFixed(2) : '—'}
                                                </td>
                                                <td className="cell-impact" style={{ color: '#d4af37' }}>
                                                    ${(trade.total_value / 1000000).toFixed(2)}M
                                                </td>
                                                <td className="cell-date">{trade.date}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={8} className="cell-empty">
                                                {insiderTrades90
                                                    ? 'No insider trades persisted in the last 90 days yet'
                                                    : 'Loading 90-day insider trading data...'}
                                            </td>
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
                                <li>
                                    <strong>Focus on BUYS, not SELLS:</strong> Insiders sell for many reasons (diversification, taxes,
                                    divorce) but they buy for ONE reason - they think the stock is going up
                                </li>
                                <li>
                                    <strong>Cluster Buying:</strong> Multiple insiders buying within the same week is extremely bullish.
                                    They're coordinating around knowledge of an upcoming catalyst.
                                </li>
                                <li>
                                    <strong>CEO/CFO Transactions:</strong> C-suite executives have the most complete picture. Weight their
                                    transactions 3x more than board members.
                                </li>
                                <li>
                                    <strong>Size Matters:</strong> $1M+ purchases are serious conviction. $5M+ is "all-in" level confidence.
                                    Compare transaction size to their existing holdings.
                                </li>
                                <li>
                                    <strong>Timing with Events:</strong> Buying before earnings or product launches is the strongest signal.
                                    Cross-reference with calendar events.
                                </li>
                                <li>
                                    <strong>Form 4 Filing Window:</strong> SEC requires filing within 2 business days. Recent filings (0-3
                                    days old) give you the freshest edge before news breaks.
                                </li>
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

                        <div
                            className="info-block"
                            style={{ marginBottom: '30px', borderLeftColor: telegramStatus?.connected ? '#00ff88' : '#ff0040' }}
                        >
                            <h3>STATUS</h3>
                            <ul>
                                <li>
                                    <strong>Authorized:</strong>{' '}
                                    {telegramStatus?.authorized === true
                                        ? 'yes'
                                        : telegramStatus?.authorized === false
                                          ? 'no - session expired, needs re-login'
                                          : 'unknown'}
                                </li>
                                <li>
                                    <strong>Backfilled on connect:</strong> {telegramStatus?.backfilled_count ?? '...'} real historical
                                    messages from the last {telegramStatus?.history_window_days ?? 30} days
                                </li>
                                {telegramStatus?.last_error && (
                                    <li>
                                        <strong>Last error:</strong> {telegramStatus.last_error}
                                    </li>
                                )}
                                <li>
                                    This is a low-frequency channel - an empty table below means the channel genuinely hasn't posted in the
                                    window, not that the connection is broken.
                                </li>
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
                                    {telegramMessages.length > 0 ? (
                                        telegramMessages.map((msg, idx) => (
                                            <tr key={idx}>
                                                <td className="cell-date">{new Date(msg.published_at).toLocaleString()}</td>
                                                <td className="cell-primary">{msg.summary || msg.title}</td>
                                                <td className="cell-tickers">{msg.tickers || '-'}</td>
                                                <td className="cell-phase">
                                                    <span
                                                        style={{
                                                            color:
                                                                msg.sentiment === 'bullish'
                                                                    ? '#00ff88'
                                                                    : msg.sentiment === 'bearish'
                                                                      ? '#ff0040'
                                                                      : '#d4af37',
                                                        }}
                                                    >
                                                        {msg.sentiment}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={4} className="cell-empty">
                                                No messages in the last {telegramStatus?.history_window_days ?? 30} days
                                            </td>
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
                                <span>
                                    <strong>Date:</strong> {dailyBrief.date}
                                </span>
                                <span>
                                    <strong>Market Regime:</strong> {dailyBrief.market_regime}
                                </span>
                                <span>
                                    <strong>Primary Catalyst:</strong> {dailyBrief.primary_catalyst}
                                </span>
                            </div>
                        </div>

                        {dailyBrief.mode && (
                            <div
                                className="data-block"
                                style={{
                                    borderLeft: `4px solid ${dailyBrief.mode === 'demo' ? '#ffa500' : '#00ff88'}`,
                                    padding: '12px 16px',
                                }}
                            >
                                <span style={{ color: dailyBrief.mode === 'demo' ? '#ffa500' : '#00ff88', fontWeight: 700 }}>
                                    {dailyBrief.mode === 'live' ? 'LIVE' : dailyBrief.mode === 'rules' ? 'RULES' : 'DEMO'}:
                                </span>{' '}
                                {dailyBrief.mode === 'demo' ? dailyBrief.demo_note : dailyBrief.data_edge}
                            </div>
                        )}

                        {dailyBrief.top_recommendations && dailyBrief.top_recommendations.length > 0 && (
                            <section className="data-block accent-panel-success">
                                <div className="block-header">
                                    <h2>⭐ TOP RECOMMENDATIONS</h2>
                                    <p>Highest-conviction picks across all categories in this brief</p>
                                </div>
                                {dailyBrief.top_recommendations.map((play, idx) => (
                                    <div key={idx} className="recommendation-card accent-success">
                                        <div className="rec-header">
                                            <h3>
                                                {play.ticker} - {play.action}
                                            </h3>
                                            <div className="rec-targets">
                                                <span className="market-cap">Target: {play.target}</span>
                                                <span className="market-cap">Stop: {play.stop}</span>
                                                <span className="confidence">Confidence: {play.confidence}</span>
                                                <span className="timeframe">Timeframe: {play.timeframe}</span>
                                            </div>
                                        </div>
                                        <div className="rec-body">
                                            <p>
                                                <strong>Rationale:</strong> {play.rationale}
                                            </p>
                                            <p>
                                                <strong>Risks:</strong> {play.risks}
                                            </p>
                                            <p>
                                                <strong>Data Sources:</strong> {play.data_sources.join(', ')}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </section>
                        )}

                        {dailyBrief.mega_cap_plays && dailyBrief.mega_cap_plays.length > 0 && (
                            <section className="data-block">
                                <div className="block-header">
                                    <h2>🏛️ MEGA-CAP PLAYS ($500B+)</h2>
                                    <p>Market-moving positions with institutional backing and major catalysts</p>
                                </div>
                                {dailyBrief.mega_cap_plays.map((play, idx) => (
                                    <div key={idx} className="recommendation-card accent-gold">
                                        <div className="rec-header">
                                            <h3>
                                                {play.ticker} - {play.action}
                                            </h3>
                                            <div className="rec-targets">
                                                <span className="market-cap">Cap: {play.market_cap}</span>
                                                <span className="confidence">Confidence: {play.confidence}</span>
                                                <span className="timeframe">Timeframe: {play.timeframe}</span>
                                            </div>
                                        </div>
                                        <div className="rec-body">
                                            <p>
                                                <strong>Catalyst:</strong> {play.catalyst}
                                            </p>
                                            <p>
                                                <strong>Smart Money Signal:</strong> {play.smart_money_signal}
                                            </p>
                                            <p>
                                                <strong>Technical Setup:</strong> {play.technical_setup}
                                            </p>
                                            <p>
                                                <strong>Risk Factor:</strong> {play.risk_factor}
                                            </p>
                                            <p>
                                                <strong>Data Sources:</strong> {play.data_sources.join(', ')}
                                            </p>
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
                                            <h3>
                                                {play.ticker} - {play.action}
                                            </h3>
                                            <div className="rec-targets">
                                                <span className="market-cap">Cap: {play.market_cap}</span>
                                                <span className="confidence">Confidence: {play.confidence}</span>
                                                <span className="timeframe">Timeframe: {play.timeframe}</span>
                                            </div>
                                        </div>
                                        <div className="rec-body">
                                            <p>
                                                <strong>Catalyst:</strong> {play.catalyst}
                                            </p>
                                            <p>
                                                <strong>Smart Money Signal:</strong> {play.smart_money_signal}
                                            </p>
                                            <p>
                                                <strong>Technical Setup:</strong> {play.technical_setup}
                                            </p>
                                            <p>
                                                <strong>Risk Factor:</strong> {play.risk_factor}
                                            </p>
                                            <p>
                                                <strong>Data Sources:</strong> {play.data_sources.join(', ')}
                                            </p>
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
                                            <h3>
                                                {play.ticker} - {play.action}
                                            </h3>
                                            <div className="rec-targets">
                                                <span className="market-cap">Cap: {play.market_cap}</span>
                                                <span className="confidence">Confidence: {play.confidence}</span>
                                                <span className="timeframe">Timeframe: {play.timeframe}</span>
                                            </div>
                                        </div>
                                        <div className="rec-body">
                                            <p>
                                                <strong>Catalyst:</strong> {play.catalyst}
                                            </p>
                                            <p>
                                                <strong>Smart Money Signal:</strong> {play.smart_money_signal}
                                            </p>
                                            <p>
                                                <strong>Technical Setup:</strong> {play.technical_setup}
                                            </p>
                                            <p>
                                                <strong>Risk Factor:</strong> {play.risk_factor}
                                            </p>
                                            <p>
                                                <strong>Data Sources:</strong> {play.data_sources.join(', ')}
                                            </p>
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
                                            <h3>
                                                {play.ticker} - {play.action}
                                            </h3>
                                            <div className="rec-targets">
                                                <span className="market-cap">Cap: {play.market_cap}</span>
                                                <span className="confidence">Confidence: {play.confidence}</span>
                                                <span className="timeframe">Timeframe: {play.timeframe}</span>
                                            </div>
                                        </div>
                                        <div className="rec-body">
                                            <p>
                                                <strong>Catalyst:</strong> {play.catalyst}
                                            </p>
                                            <p>
                                                <strong>Smart Money Signal:</strong> {play.smart_money_signal}
                                            </p>
                                            <p>
                                                <strong>Technical Setup:</strong> {play.technical_setup}
                                            </p>
                                            <p>
                                                <strong>Risk Factor:</strong> {play.risk_factor}
                                            </p>
                                            <p>
                                                <strong>Data Sources:</strong> {play.data_sources.join(', ')}
                                            </p>
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
                                            <h3>
                                                {play.tickers.join(', ')} - {play.action}
                                            </h3>
                                            <div className="rec-targets">
                                                <span className="market-cap">Cap: {play.market_cap}</span>
                                                <span className="sector">Sector: {play.sector}</span>
                                                <span className="confidence">Confidence: {play.confidence}</span>
                                                <span className="timeframe">Timeframe: {play.timeframe}</span>
                                            </div>
                                        </div>
                                        <div className="rec-body">
                                            <p>
                                                <strong>Catalyst:</strong> {play.catalyst}
                                            </p>
                                            <p>
                                                <strong>Smart Money Signal:</strong> {play.smart_money_signal}
                                            </p>
                                            <p>
                                                <strong>Technical Setup:</strong> {play.technical_setup}
                                            </p>
                                            <p>
                                                <strong>Risk Factor:</strong> {play.risk_factor}
                                            </p>
                                            <p>
                                                <strong>Data Sources:</strong> {play.data_sources.join(', ')}
                                            </p>
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

                        {dailyBrief.smart_money_activity && (
                            <section className="data-block">
                                <div className="block-header">
                                    <h2>💰 SMART MONEY ACTIVITY</h2>
                                </div>
                                <div className="context-grid">
                                    <div className="context-item">
                                        <h4>INSIDER TRADES SUMMARY</h4>
                                        <p>{dailyBrief.smart_money_activity.insider_trades_summary}</p>
                                    </div>
                                    <div className="context-item">
                                        <h4>CONGRESSIONAL TRADES</h4>
                                        <p>{dailyBrief.smart_money_activity.congressional_trades}</p>
                                    </div>
                                    <div className="context-item">
                                        <h4>INSTITUTIONAL FLOW</h4>
                                        <p>{dailyBrief.smart_money_activity.institutional_flow}</p>
                                    </div>
                                    <div className="context-item">
                                        <h4>CLUSTER BUYING ALERTS</h4>
                                        <p>{dailyBrief.smart_money_activity.cluster_buying_alerts}</p>
                                    </div>
                                </div>
                            </section>
                        )}

                        {dailyBrief.risk_management && (
                            <section className="data-block">
                                <div className="block-header">
                                    <h2>🛡️ RISK MANAGEMENT</h2>
                                </div>
                                <div className="context-grid">
                                    <div className="context-item">
                                        <h4>MARKET RISKS</h4>
                                        <p>{dailyBrief.risk_management.market_risks}</p>
                                    </div>
                                    <div className="context-item">
                                        <h4>POSITION SIZING</h4>
                                        <p>{dailyBrief.risk_management.position_sizing}</p>
                                    </div>
                                    <div className="context-item">
                                        <h4>HEDGING</h4>
                                        <p>{dailyBrief.risk_management.hedging}</p>
                                    </div>
                                    <div className="context-item">
                                        <h4>WATCH LEVELS</h4>
                                        <p>{dailyBrief.risk_management.watch_levels}</p>
                                    </div>
                                </div>
                            </section>
                        )}

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
                                <span>
                                    <strong>Model:</strong> {aiPredictions.meta.model_version}
                                </span>
                                <span>
                                    <strong>Data Sources:</strong> {aiPredictions.meta.total_data_sources}
                                </span>
                                <span>
                                    <strong>Horizon:</strong> {aiPredictions.meta.prediction_horizon}
                                </span>
                                <span>
                                    <strong>Calibration:</strong> {aiPredictions.meta.confidence_calibration}
                                </span>
                            </div>
                            {aiPredictions.meta.note && <p className="text-muted lens-note">{aiPredictions.meta.note}</p>}
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
                                        <p>
                                            <strong>Predictions Made:</strong>{' '}
                                            {aiPredictions.prediction_accuracy_stats.last_30_days.predictions_made}
                                        </p>
                                        <p>
                                            <strong>Resolved:</strong>{' '}
                                            {aiPredictions.prediction_accuracy_stats.last_30_days.predictions_resolved}
                                        </p>
                                        <p>
                                            <strong>Correct:</strong> {aiPredictions.prediction_accuracy_stats.last_30_days.correct}
                                        </p>
                                        <p className="text-success stat-big">
                                            <strong>
                                                Accuracy: {(aiPredictions.prediction_accuracy_stats.last_30_days.accuracy * 100).toFixed(1)}
                                                %
                                            </strong>
                                        </p>
                                        <p>
                                            <strong>Calibration Score:</strong>{' '}
                                            {(aiPredictions.prediction_accuracy_stats.last_30_days.calibration_score * 100).toFixed(1)}%
                                        </p>
                                    </div>
                                    <div className="context-item">
                                        <h4>BY CATEGORY (real historical backtest)</h4>
                                        {Object.entries(aiPredictions.prediction_accuracy_stats.by_category).length === 0 ? (
                                            <p className="text-muted">Backtest not computed yet - check back shortly.</p>
                                        ) : (
                                            Object.entries(aiPredictions.prediction_accuracy_stats.by_category).map(
                                                ([cat, stats]: [string, any]) => (
                                                    <p key={cat}>
                                                        <strong>{cat}:</strong> {(stats.accuracy * 100).toFixed(1)}% positive (n={stats.n})
                                                    </p>
                                                ),
                                            )
                                        )}
                                    </div>
                                    {aiPredictions.prediction_accuracy_stats.live_prediction_by_category && (
                                        <div className="context-item">
                                            <h4>BY CATEGORY (live-prediction calibration)</h4>
                                            <p className="text-muted">
                                                Resolved live predictions graded against real fetched outcomes - a different, real thing
                                                from the historical insider-buy backtest above.
                                            </p>
                                            {Object.entries(aiPredictions.prediction_accuracy_stats.live_prediction_by_category).length ===
                                            0 ? (
                                                <p className="text-muted">No resolved live predictions yet.</p>
                                            ) : (
                                                Object.entries(aiPredictions.prediction_accuracy_stats.live_prediction_by_category).map(
                                                    ([cat, stats]: [string, any]) => (
                                                        <p key={cat}>
                                                            <strong>{cat}:</strong> {(stats.accuracy * 100).toFixed(1)}% accuracy (n=
                                                            {stats.n}, correct={stats.correct})
                                                        </p>
                                                    ),
                                                )
                                            )}
                                        </div>
                                    )}
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
                                                {aiPredictions.historical_backtest.period?.end} (
                                                {aiPredictions.historical_backtest.period?.days} days) &nbsp;|&nbsp;
                                                <strong> Universe:</strong> {aiPredictions.historical_backtest.universe?.join(', ')}{' '}
                                                &nbsp;|&nbsp;
                                                <strong> Filings checked:</strong> {aiPredictions.historical_backtest.filings_checked}
                                            </p>
                                        </div>
                                        {Object.entries(aiPredictions.historical_backtest.signals).map(([sigName, sig]: [string, any]) => (
                                            <div className="context-item" key={sigName}>
                                                <h4>
                                                    {sigName.toUpperCase().replace('_', ' ')} ({sig.events_found} real events found)
                                                </h4>
                                                {sig.events_found === 0 ? (
                                                    <p>No real occurrences of this signal in the backtest window.</p>
                                                ) : (
                                                    <table className="mini-table">
                                                        <thead>
                                                            <tr>
                                                                <th>Horizon</th>
                                                                <th>Tested</th>
                                                                <th>% Positive</th>
                                                                <th>Avg Return</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {Object.entries(sig.by_horizon).map(([h, stats]: [string, any]) => (
                                                                <tr key={h}>
                                                                    <td>{h}</td>
                                                                    <td>{stats.signals_tested}</td>
                                                                    <td>{stats.pct_positive != null ? `${stats.pct_positive}%` : '—'}</td>
                                                                    <td>
                                                                        {stats.avg_return_pct != null ? `${stats.avg_return_pct}%` : '—'}
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                )}
                                                {sig.sample_events && sig.sample_events.length > 0 && (
                                                    <table className="mini-table">
                                                        <thead>
                                                            <tr>
                                                                <th>Ticker</th>
                                                                <th>Date</th>
                                                                <th>Insider(s)</th>
                                                                <th>Value</th>
                                                                <th>Returns by horizon</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {sig.sample_events.map((ev: any, i: number) => (
                                                                <tr key={i}>
                                                                    <td>{ev.ticker}</td>
                                                                    <td>{formatEventDate(ev.date)}</td>
                                                                    <td>
                                                                        {Array.isArray(ev.insider_or_insiders)
                                                                            ? ev.insider_or_insiders.join(', ')
                                                                            : ev.insider_or_insiders}
                                                                    </td>
                                                                    <td>${Number(ev.value).toLocaleString()}</td>
                                                                    <td>
                                                                        {Object.entries(ev.returns_by_horizon_pct || {}).map(
                                                                            ([h, r]: [string, any]) => (
                                                                                <span key={h} style={{ marginRight: 8 }}>
                                                                                    {h}: {r != null ? `${r}%` : '—'}
                                                                                </span>
                                                                            ),
                                                                        )}
                                                                    </td>
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
                                        <h3>
                                            {pred.ticker} - {pred.type}
                                        </h3>
                                        <div className="rec-targets">
                                            <span className="confidence tone-success">
                                                Confidence: {(pred.confidence * 100).toFixed(0)}%
                                            </span>
                                            <span className="timeframe">{pred.timeframe}</span>
                                            <span className="action-tag">{pred.action}</span>
                                        </div>
                                    </div>
                                    <div className="rec-body">
                                        <p>
                                            <strong>Prediction:</strong> {pred.prediction}
                                        </p>
                                        <p>
                                            <strong>Reasoning:</strong> {pred.reasoning}
                                        </p>
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
                                                <p className="text-success">
                                                    <strong>If Correct:</strong> {pred.predicted_outcome.if_correct}
                                                </p>
                                                <p className="text-danger">
                                                    <strong>If Wrong:</strong> {pred.predicted_outcome.if_wrong}
                                                </p>
                                                {pred.predicted_outcome.expected_value && (
                                                    <p className="text-warning">
                                                        <strong>Expected Value:</strong> {pred.predicted_outcome.expected_value}
                                                    </p>
                                                )}
                                            </div>
                                        )}
                                        {pred.adversarial_test && (
                                            <p className="text-orange" style={{ marginTop: '10px' }}>
                                                <strong>Adversarial Test:</strong> {pred.adversarial_test}
                                            </p>
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
                                        <h3>
                                            {pred.ticker} - {pred.pattern_type}
                                        </h3>
                                        <div className="rec-targets">
                                            <span className="confidence tone-info">Confidence: {(pred.confidence * 100).toFixed(0)}%</span>
                                            <span className="action-tag">{pred.action}</span>
                                        </div>
                                    </div>
                                    <div className="rec-body">
                                        <p>
                                            <strong>Prediction:</strong> {pred.prediction}
                                        </p>
                                        <p>
                                            <strong>Historical Precedent:</strong> {pred.historical_precedent}
                                        </p>
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
                                            <p className="text-success">
                                                <strong>Predicted Move:</strong> {pred.predicted_move}
                                            </p>
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
                                        <p className="text-orange">
                                            <strong>Causal Chain:</strong> {pred.causal_chain}
                                        </p>
                                        <p>
                                            <strong>Prediction:</strong> {pred.prediction}
                                        </p>
                                        <p>
                                            <strong>Reasoning:</strong> {pred.reasoning}
                                        </p>
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
                                            <div className="text-success">
                                                <strong>Predicted Outcome:</strong>
                                                {Object.entries(pred.predicted_outcome)
                                                    .filter(([, v]) => v)
                                                    .map(([k, v]) => (
                                                        <p key={k}>
                                                            {k.replace(/_/g, ' ')}: {v}
                                                        </p>
                                                    ))}
                                            </div>
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
                                        <p className="text-purple">
                                            <strong>Contrarian View:</strong> {pred.contrarian_view}
                                        </p>
                                        <p>
                                            <strong>Prediction:</strong> {pred.prediction}
                                        </p>
                                        <p>
                                            <strong>Reasoning:</strong> {pred.reasoning}
                                        </p>
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
                                            <div className="text-orange">
                                                <strong>Predicted Outcome:</strong>
                                                {Object.entries(pred.predicted_outcome)
                                                    .filter(([, v]) => v)
                                                    .map(([k, v]) => (
                                                        <p key={k}>
                                                            {k.replace(/_/g, ' ')}: {v}
                                                        </p>
                                                    ))}
                                            </div>
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
                                                {risk.probability != null
                                                    ? `Probability: ${(risk.probability * 100).toFixed(1)}%`
                                                    : 'Monitor (no probability estimated)'}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="rec-body">
                                        <p>
                                            <strong>Scenario:</strong> {risk.scenario}
                                        </p>
                                        <p className="text-danger">
                                            <strong>Impact If Occurs:</strong> {risk.impact_if_occurs}
                                        </p>
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
                                            <p className="text-success">
                                                <strong>Hedge Strategy:</strong> {risk.hedge}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </section>
                    </div>
                )}

                {view === 'calendar' && (
                    <div className="terminal-view">
                        <div className="view-header">
                            <h1>D-X COUNTDOWN CALENDAR</h1>
                            <p>
                                Real earnings and macro-release dates, sorted into 4 timing phases (Pre-rumor → Accumulation → Euforia →
                                Danger) with a rule-based entry/exit note per event
                            </p>
                            <div className="nav-pills" style={{ marginTop: 12 }}>
                                <button className={calendarMode === 'list' ? 'active' : ''} onClick={() => setCalendarMode('list')}>
                                    LIST
                                </button>
                                <button className={calendarMode === 'month' ? 'active' : ''} onClick={() => setCalendarMode('month')}>
                                    MONTH
                                </button>
                            </div>
                        </div>

                        {calendarMode === 'list' ? (
                            <section className="data-block">
                                <div className="block-header">
                                    <h2>UPCOMING CATALYSTS</h2>
                                    <p>
                                        Events labeled "(estimated date)" are honest heuristic fallbacks - the real source (Yahoo earnings
                                        calendar) was unavailable when last synced
                                    </p>
                                </div>
                                <table className="data-grid">
                                    <thead>
                                        <tr>
                                            <th>EVENT</th>
                                            <th>DATE</th>
                                            <th>D-X</th>
                                            <th>PHASE</th>
                                            <th>TICKERS</th>
                                            <th>RECOMMENDATION</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {calendarEvents.length > 0 ? (
                                            calendarEvents.map((evt) => (
                                                <tr key={evt.id}>
                                                    <td className="cell-primary">
                                                        {evt.title}
                                                        {evt.title.toLowerCase().includes('estimated date') && (
                                                            <span style={{ color: '#888888', fontSize: '0.85em' }}> (est.)</span>
                                                        )}
                                                    </td>
                                                    <td className="cell-date">{formatEventDate(evt.date)}</td>
                                                    <td className="cell-countdown" style={{ color: evt.phase_color, fontWeight: 700 }}>
                                                        {evt.days_until <= 0 ? 'LIVE' : `D-${evt.days_until}`}
                                                    </td>
                                                    <td className="cell-phase">
                                                        <span style={{ color: evt.phase_color, fontWeight: 700 }}>
                                                            {evt.phase.toUpperCase()}
                                                        </span>
                                                    </td>
                                                    <td className="cell-tickers">
                                                        {(evt.affected_tickers || []).map((t) => (
                                                            <button key={t} className="ticker-link" onClick={() => openLens(t)}>
                                                                {t}
                                                            </button>
                                                        ))}
                                                    </td>
                                                    <td className="cell-rec">{evt.recommendation}</td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={6} className="cell-empty">
                                                    Loading calendar events...
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </section>
                        ) : (
                            <section className="data-block">
                                <div className="block-header">
                                    <h2>
                                        <button
                                            className="month-nav-btn"
                                            onClick={() => {
                                                const m = viewMonth === 0 ? 11 : viewMonth - 1;
                                                setViewMonth(m);
                                                setViewYear(m === 11 ? viewYear - 1 : viewYear);
                                            }}
                                        >
                                            ‹
                                        </button>{' '}
                                        {new Date(viewYear, viewMonth, 1).toLocaleString('en-US', { month: 'long', year: 'numeric' })}{' '}
                                        <button
                                            className="month-nav-btn"
                                            onClick={() => {
                                                const m = viewMonth === 11 ? 0 : viewMonth + 1;
                                                setViewMonth(m);
                                                setViewYear(m === 0 ? viewYear + 1 : viewYear);
                                            }}
                                        >
                                            ›
                                        </button>
                                    </h2>
                                    <p>Click a pill to see the event's D-X, phase, and recommendation</p>
                                </div>
                                {(() => {
                                    const firstOfMonth = new Date(viewYear, viewMonth, 1);
                                    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
                                    const startWeekday = firstOfMonth.getDay();
                                    const eventsByDay: { [day: number]: CalendarEvent[] } = {};
                                    calendarEvents.forEach((evt) => {
                                        const d = new Date(evt.date);
                                        if (d.getFullYear() === viewYear && d.getMonth() === viewMonth) {
                                            const day = d.getDate();
                                            if (!eventsByDay[day]) eventsByDay[day] = [];
                                            eventsByDay[day].push(evt);
                                        }
                                    });
                                    const cells: (number | null)[] = [];
                                    for (let i = 0; i < startWeekday; i++) cells.push(null);
                                    for (let day = 1; day <= daysInMonth; day++) cells.push(day);

                                    return (
                                        <div>
                                            <div className="calendar-grid-header">
                                                {['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map((d) => (
                                                    <div key={d} className="calendar-grid-header-cell">
                                                        {d}
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="calendar-grid">
                                                {cells.map((day, idx) => (
                                                    <div
                                                        key={idx}
                                                        className={day ? 'calendar-day-cell' : 'calendar-day-cell calendar-day-empty'}
                                                    >
                                                        {day && (
                                                            <>
                                                                <div className="calendar-day-number">{day}</div>
                                                                {(eventsByDay[day] || []).map((evt) => (
                                                                    <div
                                                                        key={evt.id}
                                                                        className="calendar-event-pill"
                                                                        style={{ backgroundColor: evt.phase_color }}
                                                                        title={`${evt.title} — ${evt.days_until <= 0 ? 'LIVE' : `D-${evt.days_until}`} (${evt.phase}) — ${evt.recommendation}`}
                                                                    >
                                                                        {evt.title.length > 18 ? evt.title.slice(0, 18) + '…' : evt.title}
                                                                    </div>
                                                                ))}
                                                            </>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })()}
                            </section>
                        )}
                    </div>
                )}

                {view === 'sources' && (
                    <div className="terminal-view">
                        <div className="view-header">
                            <h1>DATA SOURCES</h1>
                            <p>Real, live status of every data source this app actually calls - never simulated</p>
                            {sourcesStatus && (
                                <div className="header-metrics">
                                    <div className="metric">
                                        <span className="metric-value">{sourcesStatus.summary.total_sources}</span>
                                        <span className="metric-label">TOTAL SOURCES</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-value">{sourcesStatus.summary.active_now}</span>
                                        <span className="metric-label">ACTIVE NOW</span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-value">{(sourcesStatus.summary.avg_success_rate * 100).toFixed(0)}%</span>
                                        <span className="metric-label">AVG SUCCESS RATE</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        <section className="data-block">
                            <div className="block-header">
                                <h2>SOURCE STATUS</h2>
                                <p>Success rate and last outcome accumulated since this backend process started</p>
                            </div>
                            <table className="data-grid">
                                <thead>
                                    <tr>
                                        <th>SOURCE</th>
                                        <th>CATEGORY</th>
                                        <th>STATUS</th>
                                        <th>SUCCESS RATE</th>
                                        <th>LAST SUCCESS</th>
                                        <th>LAST ERROR</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {sourcesStatus && sourcesStatus.sources.length > 0 ? (
                                        sourcesStatus.sources.map((src, idx) => (
                                            <tr key={idx}>
                                                <td className="cell-primary">{src.name}</td>
                                                <td className="cell-type">{src.category || '—'}</td>
                                                <td className="cell-phase">
                                                    <span
                                                        style={{
                                                            color:
                                                                src.status === 'active'
                                                                    ? '#00ff88'
                                                                    : src.status === 'degraded'
                                                                      ? '#ffa500'
                                                                      : '#ff0040',
                                                            fontWeight: 700,
                                                        }}
                                                    >
                                                        {src.status.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="cell-impact">
                                                    {src.success_rate != null ? `${(src.success_rate * 100).toFixed(0)}%` : '—'}
                                                </td>
                                                <td className="cell-date">
                                                    {src.last_success_at ? new Date(src.last_success_at).toLocaleString() : 'never'}
                                                </td>
                                                <td className="cell-rec">{src.last_error || '—'}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={6} className="cell-empty">
                                                Loading source status...
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </section>
                    </div>
                )}

                {view === 'volatility' && (
                    <div className="terminal-view">
                        <div className="view-header">
                            <h1>VOLATILITY</h1>
                            <p>
                                Real VIX, Fear &amp; Greed, and Reddit sentiment readings, plus upcoming high-phase calendar events as
                                volatility catalysts
                            </p>
                        </div>

                        <section className="data-block">
                            <div className="block-header">
                                <h2>SENTIMENT READINGS</h2>
                            </div>
                            <div className="header-metrics">
                                <div className="metric">
                                    <span className="metric-value">
                                        {volatility?.vix?.value != null ? volatility.vix.value.toFixed(1) : 'N/A'}
                                    </span>
                                    <span className="metric-label">VIX ({volatility?.vix?.bucket || 'Unknown'})</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{volatility?.fear_greed?.value ?? 'N/A'}</span>
                                    <span className="metric-label">FEAR &amp; GREED ({volatility?.fear_greed?.rating || 'Unknown'})</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{volatility?.reddit_sentiment?.value ?? 'N/A'}</span>
                                    <span className="metric-label">REDDIT SENTIMENT (r/wallstreetbets)</span>
                                </div>
                            </div>
                        </section>

                        <section className="data-block">
                            <div className="block-header">
                                <h2>VOLATILITY CATALYSTS AHEAD</h2>
                                <p>Real upcoming events already in the danger or euforia phase - not a fabricated impact score</p>
                            </div>
                            <table className="data-grid">
                                <thead>
                                    <tr>
                                        <th>EVENT</th>
                                        <th>DATE</th>
                                        <th>D-X</th>
                                        <th>PHASE</th>
                                        <th>TICKERS</th>
                                        <th>RECOMMENDATION</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {volatility && volatility.volatility_catalysts.length > 0 ? (
                                        volatility.volatility_catalysts.map((evt) => (
                                            <tr key={evt.id}>
                                                <td className="cell-primary">{evt.title}</td>
                                                <td className="cell-date">{formatEventDate(evt.date)}</td>
                                                <td className="cell-countdown" style={{ color: evt.phase_color, fontWeight: 700 }}>
                                                    {evt.days_until <= 0 ? 'LIVE' : `D-${evt.days_until}`}
                                                </td>
                                                <td className="cell-phase">
                                                    <span style={{ color: evt.phase_color, fontWeight: 700 }}>
                                                        {evt.phase.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="cell-tickers">
                                                    {(evt.affected_tickers || []).map((t) => (
                                                        <button key={t} className="ticker-link" onClick={() => openLens(t)}>
                                                            {t}
                                                        </button>
                                                    ))}
                                                </td>
                                                <td className="cell-rec">{evt.recommendation}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={6} className="cell-empty">
                                                No danger/euforia-phase catalysts in the current window
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </section>
                    </div>
                )}
            </main>
        </div>
    );
}

export default Intelligence;
