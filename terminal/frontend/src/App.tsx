import { useEffect, useState, useCallback } from 'react';
import './App.css';

const API = 'http://localhost:8000';
const WATCH = ['AAPL', 'NVDA', 'TSLA', 'ORCL', 'RDDT', 'MSFT'];

type Quote = {
    ticker: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
    marketCap: number;
    pe: number;
    volume: number;
    high52: number;
    low52: number;
};

type MarketEvent = {
    id: number;
    title: string;
    category: string;
    event_date: string;
    affected_assets: string[];
};

type AssetSentiment = {
    ticker: string;
    avg_sentiment: number;
    event_count: number;
};

function daysUntil(dateStr: string) {
    const d = Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86400000);
    if (d < 0) return 'PAST';
    if (d === 0) return 'D-0';
    return `D-${d}`;
}

function sentColor(score: number) {
    if (score > 0.15) return 'var(--success)';
    if (score < -0.15) return 'var(--danger)';
    return 'var(--warning)';
}

export default function App() {
    const [quotes, setQuotes] = useState<Record<string, Quote>>({});
    const [events, setEvents] = useState<MarketEvent[]>([]);
    const [sentiment, setSentiment] = useState<AssetSentiment[]>([]);
    const [focus, setFocus] = useState<Quote | null>(null);
    const [searchVal, setSearchVal] = useState('');
    const [now, setNow] = useState(new Date());
    const [connected, setConnected] = useState(true);

    const fetchQuotes = useCallback(async () => {
        try {
            const results = await Promise.all(WATCH.map((t) => fetch(`${API}/market/quote/${t}`).then((r) => (r.ok ? r.json() : null))));
            const map: Record<string, Quote> = {};
            results.forEach((q, i) => {
                if (q) map[WATCH[i]] = { ...q, ticker: WATCH[i] };
            });
            setQuotes(map);
            setConnected(true);
        } catch {
            setConnected(false);
        }
    }, []);

    const fetchEvents = useCallback(async () => {
        try {
            const r = await fetch(`${API}/api/market-events`);
            const d = await r.json();
            setEvents((d.events ?? []).slice(0, 12));
        } catch {
            /* ignore */
        }
    }, []);

    const fetchSentiment = useCallback(async () => {
        try {
            const r = await fetch(`${API}/api/sentiment/scan?timeframe=week`);
            const d = await r.json();
            const list = (d.asset_sentiment ?? []) as AssetSentiment[];
            setSentiment(list.sort((a, b) => b.event_count - a.event_count).slice(0, 10));
        } catch {
            /* ignore */
        }
    }, []);

    const lookup = useCallback(async (ticker: string) => {
        const t = ticker.trim().toUpperCase();
        if (!t) return;
        try {
            const r = await fetch(`${API}/market/quote/${t}`);
            if (r.ok) setFocus({ ...(await r.json()), ticker: t });
        } catch {
            /* ignore */
        }
    }, []);

    useEffect(() => {
        fetchQuotes();
        fetchEvents();
        fetchSentiment();
        const qi = setInterval(fetchQuotes, 15000);
        const ei = setInterval(fetchEvents, 30000);
        const si = setInterval(fetchSentiment, 30000);
        const ci = setInterval(() => setNow(new Date()), 1000);
        return () => {
            clearInterval(qi);
            clearInterval(ei);
            clearInterval(si);
            clearInterval(ci);
        };
    }, [fetchQuotes, fetchEvents, fetchSentiment]);

    return (
        <div className="term">
            <div className="bar">
                <div className="brand">
                    <span className="mark">A</span>AEON TERMINAL
                </div>
                <div className="search">
                    <input
                        placeholder="TICKER"
                        value={searchVal}
                        onChange={(e) => setSearchVal(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && lookup(searchVal)}
                    />
                    <button onClick={() => lookup(searchVal)}>GO</button>
                </div>
                <div className="status">
                    <span className={`dot ${connected ? 'up' : 'down'}`} />
                    {connected ? 'LIVE' : 'RECONNECTING'}
                    <span className="clock">{now.toLocaleTimeString()}</span>
                </div>
            </div>

            <div className="tape">
                {WATCH.map((t) => {
                    const q = quotes[t];
                    const up = (q?.change ?? 0) >= 0;
                    return (
                        <div className="tape-item" key={t}>
                            <span className="t">{t}</span>
                            <span className="p">{q ? `$${q.price.toFixed(2)}` : '···'}</span>
                            {q && (
                                <span className={`c ${up ? 'up' : 'down'}`}>
                                    {up ? '▲' : '▼'} {q.changePercent.toFixed(2)}%
                                </span>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className="grid">
                <div className="panel">
                    <div className="panel-head">
                        <h3>Market Events</h3>
                        <span className="n">{events.length} upcoming</span>
                    </div>
                    <div className="panel-body">
                        {events.length === 0 && <div className="loading">syncing events…</div>}
                        {events.map((e) => (
                            <div className="event-row" key={e.id}>
                                <div className="dcount">{daysUntil(e.event_date)}</div>
                                <div className="body">
                                    <div className="title">{e.title}</div>
                                    <div className="meta">
                                        <span className="pill">{e.category}</span>
                                        {(e.affected_assets ?? []).slice(0, 4).map((a) => (
                                            <span className="pill tick" key={a} onClick={() => lookup(a)} style={{ cursor: 'pointer' }}>
                                                {a}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <div className="panel">
                        <div className="panel-head">
                            <h3>Smart Money / Sentiment Scan</h3>
                            <span className="n">7d window</span>
                        </div>
                        <div className="panel-body" style={{ maxHeight: '32vh' }}>
                            {sentiment.length === 0 && <div className="loading">scanning sentiment…</div>}
                            {sentiment.map((s) => {
                                const pct = Math.min(100, Math.abs(s.avg_sentiment) * 100);
                                return (
                                    <div className="sent-row" key={s.ticker} onClick={() => lookup(s.ticker)} style={{ cursor: 'pointer' }}>
                                        <div className="tk">{s.ticker}</div>
                                        <div className="sent-bar">
                                            <div
                                                className="fill"
                                                style={{
                                                    width: `${pct}%`,
                                                    left: s.avg_sentiment >= 0 ? '50%' : `${50 - pct}%`,
                                                    background: sentColor(s.avg_sentiment),
                                                }}
                                            />
                                        </div>
                                        <div className="score" style={{ color: sentColor(s.avg_sentiment) }}>
                                            {s.avg_sentiment > 0 ? '+' : ''}
                                            {s.avg_sentiment.toFixed(2)}
                                        </div>
                                        <div className="cnt">{s.event_count} evt</div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    <div className="panel" style={{ borderTop: '1px solid var(--border)' }}>
                        <div className="panel-head">
                            <h3>Ticker Focus</h3>
                            <span className="n">quote lookup</span>
                        </div>
                        {focus ? (
                            <div className="quote-card">
                                <div className="top">
                                    <div>
                                        <div className="tk">{focus.ticker}</div>
                                        <div className="name">{focus.name}</div>
                                    </div>
                                    <div>
                                        <span className="price">${focus.price?.toFixed(2)}</span>
                                        <span className={`chg ${focus.change >= 0 ? 'up' : 'down'}`}>
                                            {focus.change >= 0 ? '▲' : '▼'} {focus.changePercent?.toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                                <div className="stats">
                                    <div className="stat">
                                        Mkt Cap<b>${(focus.marketCap / 1e9).toFixed(1)}B</b>
                                    </div>
                                    <div className="stat">
                                        P/E<b>{focus.pe?.toFixed(1) ?? '—'}</b>
                                    </div>
                                    <div className="stat">
                                        Volume<b>{(focus.volume / 1e6).toFixed(1)}M</b>
                                    </div>
                                    <div className="stat">
                                        52w High<b>${focus.high52?.toFixed(2)}</b>
                                    </div>
                                    <div className="stat">
                                        52w Low<b>${focus.low52?.toFixed(2)}</b>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="empty">Search a ticker, or click one from Events / Sentiment above.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
