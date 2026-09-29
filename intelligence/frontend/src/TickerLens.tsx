/**
 * Ticker Lens — everything Intelligence knows about one ticker on one screen:
 * the timing read from its nearest dated catalyst, the D-X event list, news and
 * Telegram mentions, 90-day insider trades, live signals and AI calls. Aeon
 * Analysis deep-links here with ?ticker=, so "check the timing for this name"
 * lands on the name instead of the generic dashboard.
 */
import { useEffect, useState } from 'react';
import { formatEventDate, formatMoney, timeAgo } from './format';

type LensEvent = {
    id: number;
    title: string;
    date: string;
    event_type: string;
    days_until: number;
    phase: string;
    phase_color: string;
    recommendation: string;
    source?: string;
};
type LensNews = { title: string; source: string; url?: string; published_at: string; sentiment: string };
type LensTrade = { insider_name: string; role: string; transaction_type: string; total_value: number; shares: number; date: string };
type LensSignal = { id: number; signal_type: string; phase: string; confidence: number; reasoning: string };
type LensPrediction = { category: string; prediction?: string; action?: string; confidence?: number; timeframe?: string };
type Lens = {
    ticker: string;
    price: number | null;
    timing: { phase: string | null; headline: string; detail: string; estimated_date: boolean };
    events: LensEvent[];
    news: LensNews[];
    news_tone: Record<string, number>;
    insider: { trades: LensTrade[]; buys: number; sells: number; buy_value: number; sell_value: number };
    signals: LensSignal[];
    predictions: LensPrediction[];
    ai_mode: string | null;
};

const PHASE_LABEL: Record<string, string> = {
    'pre-rumor': 'PRE-RUMOR',
    accumulation: 'ACCUMULATION',
    euforia: 'EUFORIA',
    danger: 'DANGER',
    live: 'LIVE',
};

export default function TickerLens({ apiBase, ticker, onTicker }: { apiBase: string; ticker: string; onTicker: (t: string) => void }) {
    const [data, setData] = useState<Lens | null>(null);
    const [err, setErr] = useState('');
    const [input, setInput] = useState(ticker);

    useEffect(() => setInput(ticker), [ticker]);

    useEffect(() => {
        if (!ticker) return;
        let cancelled = false;
        setData(null);
        setErr('');
        fetch(`${apiBase}/api/ticker/${encodeURIComponent(ticker)}`)
            .then(async (r) => {
                if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
                return r.json();
            })
            .then((d) => !cancelled && setData(d))
            .catch((e) => !cancelled && setErr(String(e instanceof Error ? e.message : e)));
        return () => {
            cancelled = true;
        };
    }, [apiBase, ticker]);

    const submit = (e: React.FormEvent) => {
        e.preventDefault();
        const t = input.trim().toUpperCase();
        if (t) onTicker(t);
    };

    const tone = data?.news_tone ?? {};
    const toneTotal = (tone.bullish ?? 0) + (tone.neutral ?? 0) + (tone.bearish ?? 0);

    return (
        <div className="terminal-view">
            <div className="view-header">
                <h1>TICKER LENS{ticker ? ` · ${ticker}` : ''}</h1>
                <p>Timing, catalysts, news, insider activity and signals for one name, from the same live data as every other tab.</p>
                <form className="lens-search" onSubmit={submit}>
                    <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ticker, e.g. NVDA" aria-label="Ticker" />
                    <button type="submit">OPEN</button>
                </form>
            </div>

            {!ticker && <p className="text-muted">Enter a ticker to open its lens.</p>}
            {err && (
                <p className="text-danger">
                    Couldn't load {ticker}: {err}
                </p>
            )}
            {ticker && !data && !err && <p className="text-muted">Loading {ticker}…</p>}

            {data && (
                <>
                    <section className="data-block">
                        <div className={`lens-timing phase-${data.timing.phase ?? 'none'}`}>
                            <div>
                                <div className="stat-label">Timing read</div>
                                <div className="lens-headline">{data.timing.headline}</div>
                                <div className="text-muted">{data.timing.detail}</div>
                                {data.timing.estimated_date && (
                                    <div className="text-warning lens-note">
                                        The date is an estimate — the company hasn't confirmed it, so treat the countdown as approximate.
                                    </div>
                                )}
                            </div>
                            <div className="header-metrics">
                                <div className="metric">
                                    <span className="metric-value">{data.price != null ? `$${data.price.toFixed(2)}` : '—'}</span>
                                    <span className="metric-label">Last price</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{data.events.length}</span>
                                    <span className="metric-label">Catalysts · 90d</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">
                                        {data.insider.buys}/{data.insider.sells}
                                    </span>
                                    <span className="metric-label">Insider buys/sells · 90d</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{data.news.length}</span>
                                    <span className="metric-label">News mentions · 30d</span>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="data-block">
                        <div className="block-header">
                            <h2>DATED CATALYSTS</h2>
                            <p>Every calendar event tagged with {data.ticker}, with its D-X countdown and phase.</p>
                        </div>
                        <table className="data-grid">
                            <thead>
                                <tr>
                                    <th>EVENT</th>
                                    <th>DATE</th>
                                    <th>D-X</th>
                                    <th>PHASE</th>
                                    <th>NOTE</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.events.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="cell-empty">
                                            No dated catalyst tagged with {data.ticker} in the next 90 days.
                                        </td>
                                    </tr>
                                )}
                                {data.events.map((e) => (
                                    <tr key={e.id}>
                                        <td className="cell-primary">{e.title}</td>
                                        <td className="cell-date">{formatEventDate(e.date)}</td>
                                        <td className="cell-countdown" style={{ color: e.phase_color }}>
                                            D-{e.days_until}
                                        </td>
                                        <td className="cell-phase" style={{ color: e.phase_color }}>
                                            {PHASE_LABEL[e.phase] ?? e.phase}
                                        </td>
                                        <td className="cell-rec">{e.recommendation}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </section>

                    <div className="lens-columns">
                        <section className="data-block">
                            <div className="block-header">
                                <h2>NEWS & TELEGRAM</h2>
                                <p>
                                    {toneTotal
                                        ? `Tone of the latest ${toneTotal}: ${tone.bullish ?? 0} bullish · ${tone.neutral ?? 0} neutral · ${tone.bearish ?? 0} bearish (keyword classifier).`
                                        : 'Headlines that name this ticker.'}
                                </p>
                            </div>
                            <table className="data-grid news-grid">
                                <tbody>
                                    {data.news.length === 0 && (
                                        <tr>
                                            <td className="cell-empty">No headlines mention {data.ticker} in the last 30 days.</td>
                                        </tr>
                                    )}
                                    {data.news.slice(0, 15).map((n, i) => (
                                        <tr key={`${n.title}-${i}`}>
                                            <td className="cell-time">{timeAgo(n.published_at)}</td>
                                            <td className="cell-news">
                                                {n.url ? (
                                                    <a href={n.url} target="_blank" rel="noreferrer">
                                                        {n.title}
                                                    </a>
                                                ) : (
                                                    n.title
                                                )}
                                                <div className="text-muted lens-source">{n.source}</div>
                                            </td>
                                            <td
                                                className={`cell-sentiment tone-${n.sentiment === 'bullish' ? 'success' : n.sentiment === 'bearish' ? 'danger' : 'info'}`}
                                            >
                                                {n.sentiment}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </section>

                        <section className="data-block">
                            <div className="block-header">
                                <h2>INSIDER TRADES · 90D</h2>
                                <p>
                                    Open-market SEC Form 4 purchases and sales only.
                                    {data.insider.buys + data.insider.sells > 0 &&
                                        ` Bought ${formatMoney(data.insider.buy_value)} · sold ${formatMoney(data.insider.sell_value)}.`}
                                </p>
                            </div>
                            <table className="data-grid">
                                <tbody>
                                    {data.insider.trades.length === 0 && (
                                        <tr>
                                            <td className="cell-empty">
                                                No open-market insider trades recorded for {data.ticker} in 90 days.
                                            </td>
                                        </tr>
                                    )}
                                    {data.insider.trades.slice(0, 12).map((t, i) => (
                                        <tr key={`${t.insider_name}-${t.date}-${i}`}>
                                            <td className="cell-date">{t.date}</td>
                                            <td className="cell-primary">
                                                {t.insider_name}
                                                <div className="text-muted lens-source">{t.role}</div>
                                            </td>
                                            <td className={t.transaction_type === 'BUY' ? 'text-success' : 'text-danger'}>
                                                {t.transaction_type}
                                            </td>
                                            <td className="cell-impact">{formatMoney(t.total_value)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </section>
                    </div>

                    <section className="data-block">
                        <div className="block-header">
                            <h2>SIGNALS & AI CALLS</h2>
                            <p>
                                Rule-based signals that mention {data.ticker}, plus AI predictions
                                {data.ai_mode === 'live' ? '' : ' (AI engine is in demo mode — no live predictions)'}.
                            </p>
                        </div>
                        <table className="data-grid">
                            <tbody>
                                {data.signals.length === 0 && data.predictions.length === 0 && (
                                    <tr>
                                        <td className="cell-empty">No active signal or AI call for {data.ticker}.</td>
                                    </tr>
                                )}
                                {data.signals.map((s) => (
                                    <tr key={`s${s.id}`}>
                                        <td className="cell-type">{s.signal_type.toUpperCase()}</td>
                                        <td className="cell-phase">{s.phase}</td>
                                        <td className="cell-countdown">{s.confidence}%</td>
                                        <td className="cell-rec">{s.reasoning}</td>
                                    </tr>
                                ))}
                                {data.predictions.map((p, i) => (
                                    <tr key={`p${i}`}>
                                        <td className="cell-type">{p.category.replace(/_/g, ' ').toUpperCase()}</td>
                                        <td className="cell-phase">{p.action ?? '—'}</td>
                                        <td className="cell-countdown">
                                            {p.confidence != null ? `${Math.round(p.confidence * 100)}%` : '—'}
                                        </td>
                                        <td className="cell-rec">
                                            {p.prediction}
                                            {p.timeframe ? ` · ${p.timeframe}` : ''}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </section>
                </>
            )}
        </div>
    );
}
