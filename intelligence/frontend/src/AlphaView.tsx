/**
 * Alpha — the strategies that turn Intelligence's data into trades, with the
 * evidence for each: live signals (entry / stop / target / exit), every strategy's
 * backtest against the S&P 500, and the forward paper-trading record built from
 * every signal the engine has issued.
 */
import { useEffect, useMemo, useState } from 'react';
import { formatEventDate } from './format';

type Signal = {
    key: string;
    strategy: string;
    strategy_name: string;
    ticker: string;
    company?: string;
    entry_price: number;
    entry_date: string;
    stop: number;
    target: number;
    exit_date: string;
    risk_reward: number | null;
    confidence: number | null;
    backtest_edge: boolean;
    tier?: 'trade' | 'watch';
    reason: string;
};
type BtEvent = {
    ticker: string;
    event_date: string;
    entry_date: string;
    exit_date: string;
    return_pct: number;
    spy_return_pct: number;
    excess_pct: number;
};
type Strategy = {
    name: string;
    thesis: string;
    rules: string;
    n?: number;
    win_rate?: number;
    avg_return_pct?: number;
    avg_excess_pct?: number;
    median_excess_pct?: number;
    t_stat?: number;
    first_half_excess_pct?: number | null;
    second_half_excess_pct?: number | null;
    verdict?: string;
    edge?: boolean;
    period?: { start: string; end: string };
    sample_events?: BtEvent[];
};
type Position = {
    id: number;
    strategy: string;
    ticker: string;
    entry_date: string;
    entry_price: number;
    planned_exit: string;
    stop: number;
    target: number;
    last_price?: number;
    unrealized_pct?: number;
    unrealized_excess_pct?: number;
    exit_date?: string;
    return_pct?: number;
    excess_pct?: number;
    exit_reason?: string;
};
type Alpha = {
    status: string | null;
    generated_at: string | null;
    backtested_at: string | null;
    errors?: Record<string, string>;
    signals: Signal[];
    strategies: Record<string, Strategy>;
    portfolio: {
        open: Position[];
        closed: Position[];
        stats: { open: number; closed: number; win_rate?: number; avg_return_pct?: number; avg_excess_pct?: number };
        equity: { date: string; cumulative_excess_pct: number; ticker: string }[];
        started: string | null;
    };
    disclaimer: string;
};

const pct = (v: number | null | undefined, signed = true) => (v == null ? '—' : `${signed && v > 0 ? '+' : ''}${v.toFixed(2)}%`);
const tone = (v: number | null | undefined) => (v == null ? '' : v > 0 ? 'text-success' : v < 0 ? 'text-danger' : '');

function verdictClass(s: Strategy): string {
    if (!s.n || s.n < 20) return 'verdict-thin';
    if (s.edge) return 'verdict-edge';
    return (s.avg_excess_pct ?? 0) > 0 ? 'verdict-weak' : 'verdict-none';
}

/** Cumulative excess return of closed paper trades — one series, zero baseline, hover readout. */
function EquityCurve({ points }: { points: Alpha['portfolio']['equity'] }) {
    const [hover, setHover] = useState<number | null>(null);
    const W = 760,
        H = 180,
        P = 34;
    const ys = points.map((p) => p.cumulative_excess_pct);
    const lo = Math.min(0, ...ys),
        hi = Math.max(0, ...ys);
    const span = hi - lo || 1;
    const x = (i: number) => P + (i / Math.max(1, points.length - 1)) * (W - 2 * P);
    const y = (v: number) => H - P - ((v - lo) / span) * (H - 2 * P);
    const d = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.cumulative_excess_pct).toFixed(1)}`).join(' ');
    const h = hover != null ? points[hover] : null;
    return (
        <div className="equity-wrap">
            <svg
                viewBox={`0 0 ${W} ${H}`}
                className="equity-chart"
                role="img"
                aria-label="Cumulative excess return of closed paper trades versus the S&P 500"
                onMouseLeave={() => setHover(null)}
                onMouseMove={(e) => {
                    const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
                    const px = ((e.clientX - r.left) / r.width) * W;
                    const i = Math.round(((px - P) / (W - 2 * P)) * (points.length - 1));
                    setHover(Math.max(0, Math.min(points.length - 1, i)));
                }}
            >
                <line x1={P} x2={W - P} y1={y(0)} y2={y(0)} className="equity-zero" />
                <text x={P - 6} y={y(0) + 4} className="equity-axis" textAnchor="end">
                    0%
                </text>
                <text x={P - 6} y={y(hi) + 4} className="equity-axis" textAnchor="end">
                    {hi.toFixed(0)}%
                </text>
                {lo < 0 && (
                    <text x={P - 6} y={y(lo) + 4} className="equity-axis" textAnchor="end">
                        {lo.toFixed(0)}%
                    </text>
                )}
                <path d={d} className="equity-line" />
                {h && (
                    <>
                        <line x1={x(hover!)} x2={x(hover!)} y1={P / 2} y2={H - P} className="equity-cross" />
                        <circle cx={x(hover!)} cy={y(h.cumulative_excess_pct)} r={4} className="equity-dot" />
                    </>
                )}
            </svg>
            <div className="equity-readout">
                {h
                    ? `${formatEventDate(h.date)} · closed ${h.ticker} · cumulative ${pct(h.cumulative_excess_pct)} vs S&P 500`
                    : `${points.length} closed trades · cumulative ${pct(points[points.length - 1]?.cumulative_excess_pct)} vs S&P 500`}
            </div>
        </div>
    );
}

export default function AlphaView({ apiBase, onTicker }: { apiBase: string; onTicker: (t: string) => void }) {
    const [data, setData] = useState<Alpha | null>(null);
    const [err, setErr] = useState('');
    const [open, setOpen] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        const load = () =>
            fetch(`${apiBase}/api/alpha`)
                .then(async (r) => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
                .then((d) => {
                    if (!cancelled) {
                        setData(d);
                        setErr('');
                    }
                })
                .catch((e) => !cancelled && setErr(String(e instanceof Error ? e.message : e)));
        load();
        const id = setInterval(() => document.visibilityState === 'visible' && load(), 120000);
        return () => {
            cancelled = true;
            clearInterval(id);
        };
    }, [apiBase]);

    const strategies = useMemo(() => Object.entries(data?.strategies ?? {}), [data]);
    const book = data?.portfolio;

    return (
        <div className="terminal-view">
            <div className="view-header">
                <h1>ALPHA</h1>
                <p>
                    Four rule-based strategies, each with its measured edge against the S&amp;P 500, turned into live trades with an entry,
                    stop, target and exit date — and a forward paper-trading record that grades every one of them.
                </p>
                {data && (
                    <div className="brief-meta">
                        <span>
                            <strong>Signals refreshed:</strong>{' '}
                            {data.generated_at ? new Date(data.generated_at).toLocaleString() : 'pending'}
                        </span>
                        <span>
                            <strong>Backtests:</strong>{' '}
                            {data.backtested_at ? new Date(data.backtested_at).toLocaleString() : 'running — first run takes a few minutes'}
                        </span>
                    </div>
                )}
            </div>

            {err && <p className="text-danger">Couldn&apos;t load the alpha engine: {err}</p>}
            {!data && !err && <p className="text-muted">Loading…</p>}
            {data?.errors && Object.keys(data.errors).length > 0 && (
                <p className="text-warning">
                    Some inputs failed on the last run:{' '}
                    {Object.entries(data.errors)
                        .map(([k, v]) => `${k} — ${v}`)
                        .join('; ')}
                </p>
            )}

            {data && (
                <>
                    <section className="data-block">
                        <div className="block-header">
                            <h2>LIVE SIGNALS</h2>
                            <p>
                                Proven-edge trades first. Confidence is the strategy&apos;s historical win rate against the S&amp;P 500 and
                                is only quoted when that edge is statistically significant; the rest are a capped watchlist, still
                                paper-traded so they build a forward record. Stops sit 2× the 14-day average true range below entry.
                            </p>
                        </div>
                        <table className="data-grid">
                            <thead>
                                <tr>
                                    <th>TICKER</th>
                                    <th>STRATEGY</th>
                                    <th>ENTRY</th>
                                    <th>STOP</th>
                                    <th>TARGET</th>
                                    <th>R/R</th>
                                    <th>EXIT BY</th>
                                    <th>CONFIDENCE</th>
                                    <th>WHY</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.signals.length === 0 && (
                                    <tr>
                                        <td colSpan={9} className="cell-empty">
                                            {data.generated_at
                                                ? 'No strategy has a qualifying setup right now. Signals appear the day a rule triggers.'
                                                : 'The engine is running its first pass…'}
                                        </td>
                                    </tr>
                                )}
                                {data.signals.map((s) => (
                                    <tr key={s.key}>
                                        <td className="cell-tickers">
                                            <button className="ticker-link" onClick={() => onTicker(s.ticker)}>
                                                {s.ticker}
                                            </button>
                                            {s.company && <div className="text-muted lens-source">{s.company}</div>}
                                        </td>
                                        <td className="cell-type">
                                            {s.strategy_name}
                                            {s.backtest_edge ? (
                                                <div className="edge-badge">✓ proven edge</div>
                                            ) : (
                                                <div className="watch-badge">watchlist · edge not proven</div>
                                            )}
                                        </td>
                                        <td className="cell-impact">${s.entry_price.toFixed(2)}</td>
                                        <td className="cell-impact text-danger">${s.stop.toFixed(2)}</td>
                                        <td className="cell-impact text-success">${s.target.toFixed(2)}</td>
                                        <td className="cell-countdown">{s.risk_reward ?? '—'}</td>
                                        <td className="cell-date">{formatEventDate(s.exit_date)}</td>
                                        <td className="cell-countdown">{s.confidence != null ? `${s.confidence.toFixed(0)}%` : '—'}</td>
                                        <td className="cell-rec">{s.reason}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </section>

                    <section className="data-block">
                        <div className="block-header">
                            <h2>STRATEGY EVIDENCE</h2>
                            <p>
                                Each strategy replayed on the last year of real events: return over its holding window minus the S&amp;P
                                500&apos;s over the same days. An edge needs 20+ events, a t-statistic of at least 2, and a positive average
                                in both the earlier and later half of the sample.
                            </p>
                        </div>
                        <div className="strategy-grid">
                            {strategies.map(([key, s]) => (
                                <div key={key} className={`strategy-card ${verdictClass(s)}`}>
                                    <div className="strategy-head">
                                        <h3>{s.name}</h3>
                                        <span className="strategy-verdict">{s.verdict ?? 'backtest pending'}</span>
                                    </div>
                                    <p className="strategy-thesis">{s.thesis}</p>
                                    <div className="strategy-stats">
                                        <div>
                                            <span className="stat-label">Events</span>
                                            <span className="stat-num">{s.n ?? '—'}</span>
                                        </div>
                                        <div>
                                            <span className="stat-label">Beat S&amp;P</span>
                                            <span className="stat-num">{s.win_rate != null ? `${s.win_rate}%` : '—'}</span>
                                        </div>
                                        <div>
                                            <span className="stat-label">Avg excess</span>
                                            <span className={`stat-num ${tone(s.avg_excess_pct)}`}>{pct(s.avg_excess_pct)}</span>
                                        </div>
                                        <div>
                                            <span className="stat-label">t-stat</span>
                                            <span className="stat-num">{s.t_stat ?? '—'}</span>
                                        </div>
                                    </div>
                                    {s.first_half_excess_pct != null && s.second_half_excess_pct != null && (
                                        <p className="strategy-halves">
                                            Stability: avg excess{' '}
                                            <span className={tone(s.first_half_excess_pct)}>{pct(s.first_half_excess_pct)}</span> in the
                                            earlier half of events,{' '}
                                            <span className={tone(s.second_half_excess_pct)}>{pct(s.second_half_excess_pct)}</span> in the
                                            later half
                                        </p>
                                    )}
                                    <p className="strategy-rules">{s.rules}</p>
                                    {!!s.sample_events?.length && (
                                        <button className="strategy-toggle" onClick={() => setOpen(open === key ? null : key)}>
                                            {open === key ? '▾ hide' : '▸ show'} recent events
                                        </button>
                                    )}
                                    {open === key && (
                                        <table className="mini-table">
                                            <thead>
                                                <tr>
                                                    <th>Ticker</th>
                                                    <th>Event</th>
                                                    <th>Return</th>
                                                    <th>S&amp;P</th>
                                                    <th>Excess</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {s.sample_events!.map((e, i) => (
                                                    <tr key={`${e.ticker}-${e.event_date}-${i}`}>
                                                        <td>{e.ticker}</td>
                                                        <td>{e.event_date}</td>
                                                        <td className={tone(e.return_pct)}>{pct(e.return_pct)}</td>
                                                        <td>{pct(e.spy_return_pct)}</td>
                                                        <td className={tone(e.excess_pct)}>{pct(e.excess_pct)}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    )}
                                </div>
                            ))}
                        </div>
                    </section>

                    {book && (
                        <section className="data-block">
                            <div className="block-header">
                                <h2>PAPER TRACK RECORD</h2>
                                <p>
                                    Every signal is booked at its entry price the moment it appears and closed at a real price — at its stop
                                    (intraday low) or on its exit date. This record only grows forward in time; it can&apos;t be backfilled.
                                    {book.started && ` Tracking since ${new Date(book.started).toLocaleDateString()}.`}
                                </p>
                            </div>
                            <div className="header-metrics">
                                <div className="metric">
                                    <span className="metric-value">{book.stats.open}</span>
                                    <span className="metric-label">Open</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{book.stats.closed}</span>
                                    <span className="metric-label">Closed</span>
                                </div>
                                <div className="metric">
                                    <span className="metric-value">{book.stats.win_rate != null ? `${book.stats.win_rate}%` : '—'}</span>
                                    <span className="metric-label">Beat S&amp;P</span>
                                </div>
                                <div className="metric">
                                    <span className={`metric-value ${tone(book.stats.avg_excess_pct)}`}>
                                        {pct(book.stats.avg_excess_pct)}
                                    </span>
                                    <span className="metric-label">Avg excess / trade</span>
                                </div>
                            </div>
                            {book.equity.length > 1 && <EquityCurve points={book.equity} />}
                            {book.open.length > 0 && (
                                <table className="data-grid" style={{ marginTop: 18 }}>
                                    <thead>
                                        <tr>
                                            <th>OPEN</th>
                                            <th>STRATEGY</th>
                                            <th>ENTRY</th>
                                            <th>LAST</th>
                                            <th>P&amp;L</th>
                                            <th>VS S&amp;P</th>
                                            <th>STOP</th>
                                            <th>EXIT BY</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {book.open.map((p) => (
                                            <tr key={p.id}>
                                                <td className="cell-tickers">
                                                    <button className="ticker-link" onClick={() => onTicker(p.ticker)}>
                                                        {p.ticker}
                                                    </button>
                                                </td>
                                                <td className="cell-type">{data.strategies[p.strategy]?.name ?? p.strategy}</td>
                                                <td className="cell-impact">${p.entry_price.toFixed(2)}</td>
                                                <td className="cell-impact">
                                                    {p.last_price != null ? `$${p.last_price.toFixed(2)}` : '—'}
                                                </td>
                                                <td className={`cell-impact ${tone(p.unrealized_pct)}`}>{pct(p.unrealized_pct)}</td>
                                                <td className={`cell-impact ${tone(p.unrealized_excess_pct)}`}>
                                                    {pct(p.unrealized_excess_pct)}
                                                </td>
                                                <td className="cell-impact">${p.stop.toFixed(2)}</td>
                                                <td className="cell-date">{formatEventDate(p.planned_exit)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                            {book.closed.length > 0 && (
                                <table className="data-grid" style={{ marginTop: 18 }}>
                                    <thead>
                                        <tr>
                                            <th>CLOSED</th>
                                            <th>STRATEGY</th>
                                            <th>ENTRY</th>
                                            <th>EXIT</th>
                                            <th>RETURN</th>
                                            <th>VS S&amp;P</th>
                                            <th>HOW</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {book.closed.slice(0, 25).map((p) => (
                                            <tr key={p.id}>
                                                <td className="cell-tickers">{p.ticker}</td>
                                                <td className="cell-type">{data.strategies[p.strategy]?.name ?? p.strategy}</td>
                                                <td className="cell-date">{p.entry_date}</td>
                                                <td className="cell-date">{p.exit_date}</td>
                                                <td className={`cell-impact ${tone(p.return_pct)}`}>{pct(p.return_pct)}</td>
                                                <td className={`cell-impact ${tone(p.excess_pct)}`}>{pct(p.excess_pct)}</td>
                                                <td className="cell-type">{p.exit_reason === 'stop' ? 'stopped out' : 'exit date'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                            {book.open.length === 0 && book.closed.length === 0 && (
                                <p className="text-muted">No paper trades yet — the first signal the engine issues opens the book.</p>
                            )}
                        </section>
                    )}
                    <p className="text-muted lens-note">{data.disclaimer}</p>
                </>
            )}
        </div>
    );
}
