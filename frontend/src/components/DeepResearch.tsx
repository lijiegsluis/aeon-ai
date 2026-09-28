/**
 * Deep Research — native Aeon rebuild of the 11-agent research engine.
 * Calls its REST API (:8600) directly across several analysis dimensions
 * (overview, peers, earnings, performance, smart money) and renders each
 * in the terminal's own design. A room in the product, not an embedded app.
 */
import { useEffect, useState } from 'react';
import { ErrorNote } from './Terminal';
import { useStore } from '../store';

const FRA = 'http://127.0.0.1:8600/api/v1';

const SUBS = [
    ['overview', '🎯 Overview'],
    ['peers', '🏘️ Peers'],
    ['earnings', '📅 Earnings'],
    ['performance', '📈 Performance'],
    ['insiders', '🏦 Smart Money'],
] as const;
type Sub = (typeof SUBS)[number][0];

const VOTE_CLS: Record<string, string> = {
    'STRONG BUY': 'text-emerald', BUY: 'text-emerald', BEAT: 'text-emerald',
    HOLD: 'text-gold-light', NEUTRAL: 'text-gold-light', MEET: 'text-gold-light',
    SELL: 'text-rose', 'STRONG SELL': 'text-rose', AVOID: 'text-rose', MISS: 'text-rose',
};
const clsFor = (v?: string) => VOTE_CLS[(v ?? '').toUpperCase()] ?? 'text-white';
const num = (v: unknown, d = 2) => (typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toFixed(d)) : '—');
const pct = (v: unknown) => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(2)}%` : '—');
const cap = (n: unknown) => {
    if (typeof n !== 'number') return '—';
    if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
    return `$${(n / 1e6).toFixed(0)}M`;
};

/* Generic leaf flattener for the Overview dimension cards */
function flatten(obj: unknown, prefix = '', depth = 0): [string, string][] {
    if (depth > 2 || obj == null) return [];
    const out: [string, string][] = [];
    if (typeof obj !== 'object') return [[prefix || 'value', String(obj)]];
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
        const label = prefix ? `${prefix} · ${k}` : k;
        if (v != null && typeof v === 'object' && !Array.isArray(v)) out.push(...flatten(v, label, depth + 1));
        else if (Array.isArray(v)) out.push([label, v.length ? v.slice(0, 3).join(', ') : '—']);
        else out.push([label, typeof v === 'number' ? num(v) : String(v)]);
    }
    return out;
}

function useFra<T>(path: string, ticker: string) {
    const [data, setData] = useState<T | null>(null);
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState('');
    const load = async () => {
        setBusy(true); setErr(''); setData(null);
        try {
            const r = await fetch(`${FRA}${path}`);
            if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
            setData(await r.json());
        } catch (e) { setErr(`Deep Research engine unreachable — ${e}`); }
        setBusy(false);
    };
    useEffect(() => { load(); /* eslint-disable-next-line */ }, [path, ticker]);
    return { data, busy, err, reload: load };
}

function Loading({ label }: { label: string }) {
    return (
        <div className="card-cyan p-6 text-center">
            <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-accent/20 border-t-accent" />
            <p className="text-sm text-white/60">{label}</p>
        </div>
    );
}
function DimCard({ title, icon, data }: { title: string; icon: string; data: Record<string, unknown> | null }) {
    if (!data || Object.keys(data).length === 0) return null;
    const rows = flatten(data).slice(0, 18);
    return (
        <div className="card p-5">
            <h3 className="section-heading mb-3">{icon} {title}</h3>
            <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
                {rows.map(([k, v]) => (
                    <div key={k} className="flex items-baseline justify-between gap-3 border-b border-white/[0.03] pb-1.5">
                        <span className="text-xs capitalize text-white/45">{k.replace(/_/g, ' ')}</span>
                        <span className="font-mono text-sm text-white/85">{v}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ── Overview ──────────────────────────────────────────────────── */
type Analysis = { current_price: number; recommendation: string; confidence: number; summary: string;
    technical: Record<string, unknown> | null; fundamental: Record<string, unknown> | null;
    sentiment: Record<string, unknown> | null; risk: Record<string, unknown> | null; execution_time_seconds: number };

function OverviewSub({ ticker }: { ticker: string }) {
    // /analyze is a POST — dedicated effect rather than the GET hook.
    const [d, setD] = useState<Analysis | null>(null);
    const [b, setB] = useState(false); const [e, setE] = useState('');
    useEffect(() => {
        setB(true); setE(''); setD(null);
        fetch(`${FRA}/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: ticker, analysis_type: 'comprehensive' }) })
            .then(async (r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); setD(await r.json()); })
            .catch((x) => setE(`Deep Research engine unreachable — ${x}`))
            .finally(() => setB(false));
    }, [ticker]);
    if (e) return <ErrorNote msg={e} />;
    if (b || !d) return <Loading label={`Orchestrating the analyst team over ${ticker}…`} />;
    return (
        <div className="space-y-4">
            <div className="card-premium p-5">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <p className="stat-label mb-1">Recommendation</p>
                        <p className={`font-display text-3xl font-black ${clsFor(d.recommendation)}`}>{d.recommendation}</p>
                    </div>
                    <div className="text-right font-mono">
                        <p className="text-sm text-white/50">${num(d.current_price)}</p>
                        <p className="text-sm text-accent">{Math.round((d.confidence ?? 0) * 100)}% confidence</p>
                    </div>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-white/75">{d.summary}</p>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
                <DimCard title="Technical" icon="📈" data={d.technical} />
                <DimCard title="Fundamental" icon="🏦" data={d.fundamental} />
                <DimCard title="Sentiment" icon="💬" data={d.sentiment} />
                <DimCard title="Risk" icon="🛡️" data={d.risk} />
            </div>
        </div>
    );
}

/* ── Peers ─────────────────────────────────────────────────────── */
type Peers = { target: string; peer_group: string[];
    metrics: Record<string, Record<string, number>>;
    strengths: string[]; weaknesses: string[] };
function PeersSub({ ticker }: { ticker: string }) {
    const { data, busy, err } = useFra<Peers>(`/peers/${ticker}`, ticker);
    if (err) return <ErrorNote msg={err} />;
    if (busy || !data) return <Loading label={`Comparing ${ticker} against its peer group…`} />;
    const cols = [data.target, ...data.peer_group];
    const metricRows: [string, string, (v: number) => string][] = [
        ['Price', 'price', (v) => `$${num(v)}`], ['Market Cap', 'market_cap', cap],
        ['P/E', 'pe_ratio', (v) => num(v, 1)], ['Fwd P/E', 'forward_pe', (v) => num(v, 1)],
        ['PEG', 'peg_ratio', (v) => num(v, 2)], ['P/B', 'pb_ratio', (v) => num(v, 1)],
        ['P/S', 'ps_ratio', (v) => num(v, 1)], ['Profit margin', 'profit_margin', (v) => pct(v * 100)],
        ['Rev growth', 'revenue_growth', (v) => pct(v * 100)],
    ];
    return (
        <div className="space-y-4">
            <div className="card p-5 overflow-x-auto">
                <h3 className="section-heading mb-3">🏘️ Peer comparison</h3>
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-white/[0.06] text-left text-[10px] uppercase tracking-wider text-white/40">
                            <th className="px-2 py-2">Metric</th>
                            {cols.map((c) => <th key={c} className={`px-2 py-2 ${c === data.target ? 'text-accent' : ''}`}>{c}</th>)}
                        </tr>
                    </thead>
                    <tbody>
                        {metricRows.map(([label, key, fmt]) => (
                            <tr key={key} className="border-b border-white/[0.03]">
                                <td className="px-2 py-1.5 text-white/50">{label}</td>
                                {cols.map((c) => (
                                    <td key={c} className={`px-2 py-1.5 font-mono ${c === data.target ? 'text-accent' : 'text-white/80'}`}>
                                        {fmt(data.metrics[c]?.[key])}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
                {data.strengths?.length > 0 && (
                    <div className="card-cyan p-4">
                        <p className="stat-label mb-2 text-emerald">Relative strengths</p>
                        <ul className="space-y-1 text-sm text-white/75">{data.strengths.map((s, i) => <li key={i}>• {s}</li>)}</ul>
                    </div>
                )}
                {data.weaknesses?.length > 0 && (
                    <div className="card p-4">
                        <p className="stat-label mb-2 text-rose">Relative weaknesses</p>
                        <ul className="space-y-1 text-sm text-white/75">{data.weaknesses.map((s, i) => <li key={i}>• {s}</li>)}</ul>
                    </div>
                )}
            </div>
        </div>
    );
}

/* ── Earnings ──────────────────────────────────────────────────── */
type Earnings = { name: string;
    last_4_quarters: { quarter: string; eps_actual: number; eps_estimate: number; eps_surprise_pct: number; verdict: string }[];
    next_earnings?: Record<string, unknown>; earnings_quality?: Record<string, unknown>; qualitative_assessment?: string };
function EarningsSub({ ticker }: { ticker: string }) {
    const { data, busy, err } = useFra<Earnings>(`/earnings/${ticker}`, ticker);
    if (err) return <ErrorNote msg={err} />;
    if (busy || !data) return <Loading label={`Pulling ${ticker} earnings history…`} />;
    return (
        <div className="space-y-4">
            <div className="card p-5">
                <h3 className="section-heading mb-3">📅 Last 4 quarters — {data.name}</h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {data.last_4_quarters?.map((q) => (
                        <div key={q.quarter} className="card-glass p-4">
                            <p className="stat-label mb-1">{q.quarter}</p>
                            <p className="font-mono text-lg font-bold text-white">${num(q.eps_actual)} <span className="text-xs text-white/40">EPS</span></p>
                            <p className="text-xs text-white/40">est ${num(q.eps_estimate)}</p>
                            <p className={`mt-1 font-semibold ${clsFor(q.verdict)}`}>{q.verdict} {pct(q.eps_surprise_pct)}</p>
                        </div>
                    ))}
                </div>
            </div>
            {data.qualitative_assessment && (
                <div className="card-cyan p-4">
                    <p className="stat-label mb-1 text-accent">Assessment</p>
                    <p className="text-sm leading-relaxed text-white/80">{data.qualitative_assessment}</p>
                </div>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
                <DimCard title="Earnings quality" icon="✅" data={data.earnings_quality ?? null} />
                <DimCard title="Next earnings" icon="🗓️" data={data.next_earnings ?? null} />
            </div>
        </div>
    );
}

/* ── Performance ───────────────────────────────────────────────── */
type Perf = { sector: string; absolute_returns: Record<string, number>;
    benchmark_comparison?: Record<string, unknown>; risk_adjusted_metrics?: Record<string, unknown>;
    drawdown_analysis?: Record<string, unknown> };
function PerformanceSub({ ticker }: { ticker: string }) {
    const { data, busy, err } = useFra<Perf>(`/performance/${ticker}`, ticker);
    if (err) return <ErrorNote msg={err} />;
    if (busy || !data) return <Loading label={`Computing ${ticker} performance…`} />;
    const order = ['1_day', '1_week', '1_month', '3_month', '6_month', '1_year', '3_year', '5_year'];
    return (
        <div className="space-y-4">
            <div className="card p-5">
                <h3 className="section-heading mb-3">📈 Total returns · {data.sector}</h3>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {order.filter((k) => data.absolute_returns?.[k] != null).map((k) => (
                        <div key={k} className="card-glass p-3 text-center">
                            <p className="stat-label">{k.replace('_', ' ')}</p>
                            <p className={`font-mono text-lg font-bold ${data.absolute_returns[k] >= 0 ? 'text-emerald' : 'text-rose'}`}>
                                {pct(data.absolute_returns[k])}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
                <DimCard title="Risk-adjusted" icon="⚖️" data={data.risk_adjusted_metrics ?? null} />
                <DimCard title="Drawdown" icon="📉" data={data.drawdown_analysis ?? null} />
                <DimCard title="vs Benchmark" icon="🎯" data={data.benchmark_comparison ?? null} />
            </div>
        </div>
    );
}

/* ── Smart Money (insiders) ────────────────────────────────────── */
type Smart = { smart_money_signal?: { score?: number; assessment?: string } | string;
    insider_activity?: { transactions?: { name: string; title: string; transaction_type: string; shares: number; value: number | null; date: string }[] };
    institutional_activity?: Record<string, unknown> };
function InsidersSub({ ticker }: { ticker: string }) {
    const { data, busy, err } = useFra<Smart>(`/insiders/${ticker}`, ticker);
    if (err) return <ErrorNote msg={err} />;
    if (busy || !data) return <Loading label={`Tracking smart money on ${ticker}…`} />;
    const txns = data.insider_activity?.transactions ?? [];
    // signal may be a string OR an object {score, assessment}
    const sig = data.smart_money_signal;
    const sigText = typeof sig === 'string' ? sig : sig?.assessment;
    const sigScore = typeof sig === 'object' ? sig?.score : undefined;
    const bullish = (sigText ?? '').toLowerCase().includes('bull');
    const bearish = (sigText ?? '').toLowerCase().includes('bear');
    return (
        <div className="space-y-4">
            {sigText && (
                <div className="card-premium p-4">
                    <div className="flex items-center justify-between gap-3">
                        <p className="stat-label text-accent">Smart money signal</p>
                        {sigScore != null && <span className="font-mono text-sm text-white/50">score {sigScore}/100</span>}
                    </div>
                    <p className={`mt-1 font-display text-xl font-bold ${bullish ? 'text-emerald' : bearish ? 'text-rose' : 'text-gold-light'}`}>
                        {sigText}
                    </p>
                </div>
            )}
            <div className="card p-5 overflow-x-auto">
                <h3 className="section-heading mb-3">🏦 Insider transactions (90d)</h3>
                {txns.length === 0 ? <p className="text-sm text-white/40">No insider transactions in the window.</p> : (
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/[0.06] text-left text-[10px] uppercase tracking-wider text-white/40">
                                <th className="px-2 py-2">Insider</th><th className="px-2 py-2">Title</th>
                                <th className="px-2 py-2">Type</th><th className="px-2 py-2">Shares</th>
                                <th className="px-2 py-2">Value</th><th className="px-2 py-2">Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {txns.slice(0, 15).map((t, i) => (
                                <tr key={i} className="border-b border-white/[0.03]">
                                    <td className="px-2 py-1.5 text-white/80">{t.name}</td>
                                    <td className="px-2 py-1.5 text-white/50">{t.title}</td>
                                    <td className={`px-2 py-1.5 font-semibold ${t.transaction_type === 'Buy' ? 'text-emerald' : 'text-rose'}`}>{t.transaction_type}</td>
                                    <td className="px-2 py-1.5 font-mono">{t.shares?.toLocaleString?.() ?? t.shares}</td>
                                    <td className="px-2 py-1.5 font-mono text-white/60">{t.value ? cap(t.value) : '—'}</td>
                                    <td className="px-2 py-1.5 font-mono text-white/40">{t.date}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
            <DimCard title="Institutional activity" icon="🏛️" data={data.institutional_activity ?? null} />
        </div>
    );
}

export default function DeepResearch() {
    const { ticker } = useStore();
    const [sub, setSub] = useState<Sub>('overview');
    return (
        <div className="animate-fade-in space-y-4">
            <div className="flex flex-wrap items-center gap-3">
                <h2 className="section-heading">Deep Research · {ticker}</h2>
                <span className="badge-accent text-[10px]">⚡ 11-agent hierarchical RAG</span>
            </div>
            <div className="flex flex-wrap gap-1 border-b border-white/[0.06] pb-2">
                {SUBS.map(([id, label]) => (
                    <button key={id} onClick={() => setSub(id)}
                        className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${
                            sub === id ? 'bg-accent/10 text-accent' : 'text-white/40 hover:text-white/70'}`}>
                        {label}
                    </button>
                ))}
            </div>
            {sub === 'overview' && <OverviewSub ticker={ticker} />}
            {sub === 'peers' && <PeersSub ticker={ticker} />}
            {sub === 'earnings' && <EarningsSub ticker={ticker} />}
            {sub === 'performance' && <PerformanceSub ticker={ticker} />}
            {sub === 'insiders' && <InsidersSub ticker={ticker} />}
        </div>
    );
}
