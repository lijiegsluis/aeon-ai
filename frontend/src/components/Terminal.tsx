/**
 * Aeon Nimbus Terminal — unified around ONE global ticker.
 * The nav search sets it; every engine reacts to it:
 *   Overview   → fused dashboard (OpenBB + Quant + Personas at a glance)
 *   Markets    → OpenBB Platform REST API           (:6900, real)
 *   Agent Desk → TauricResearch/TradingAgents       (:8001, real LangGraph)
 *   FinRobot   → AI4Finance FinRobot native app     (:8002, real)
 *   Analyst    → financial-research-analyst-agent   (:8501, real Streamlit)
 *   Quant Lab / Personas → Aeon native analytics    (:8000)
 * Free engines auto-run on ticker change; token-burning ones prefill and wait.
 */
import { useEffect, useRef, useState } from 'react';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useStore } from '../store';
import { jget, jpost } from '../utils/api';
import { getSource } from '../dataProvenance';

const AEON = 'http://127.0.0.1:8000';
const OPENBB = 'http://127.0.0.1:6900';
const TA = 'http://127.0.0.1:8001';
export const FINROBOT_URL = 'http://127.0.0.1:8002';
export const FRA_URL = 'http://127.0.0.1:8600';

/* ─── Service status — live dots for every engine ────────────────── */
const SERVICES: [string, string, string][] = [
    ['Aeon', `${AEON}/health`, 'cors'],
    ['Markets', `${OPENBB}/docs`, 'no-cors'],
    ['Agents', `${TA}/health`, 'cors'],
    ['Deep Reports', FINROBOT_URL, 'no-cors'],
    ['Deep Research', `${FRA_URL}/health`, 'no-cors'],
    ['Worker', 'http://127.0.0.1:8787/', 'no-cors'],
];

export function ServiceStatus() {
    const [up, setUp] = useState<Record<string, boolean>>({});
    useEffect(() => {
        const ping = () => SERVICES.forEach(([name, url, mode]) =>
            fetch(url, mode === 'no-cors' ? { mode: 'no-cors' } : undefined)
                .then(() => setUp((s) => ({ ...s, [name]: true })))
                .catch(() => setUp((s) => ({ ...s, [name]: false }))));
        ping();
        const id = setInterval(ping, 20000);
        return () => clearInterval(id);
    }, []);
    return (
        <div className="hidden items-center gap-1.5 lg:flex" title={SERVICES.map(([n]) => `${n}: ${up[n] === false ? 'down' : up[n] ? 'up' : '…'}`).join('\n')}>
            {SERVICES.map(([name]) => (
                <span key={name} title={`${name}: ${up[name] === false ? 'down' : up[name] ? 'up' : 'checking'}`}
                    className={`h-2 w-2 rounded-full ${up[name] === false ? 'bg-rose' : up[name] ? 'bg-emerald' : 'bg-white/20'}`} />
            ))}
        </div>
    );
}

/** One vault, every engine: every AI-powered tab reads its key from the
 * same encrypted vault used by Research (🔑 Manage Keys in the nav) instead
 * of keeping its own separate field. Falls back to a legacy per-tab key
 * (written before this vault existed) so nothing anyone already entered
 * gets silently dropped. */
export function useVaultKey(provider: 'gemini' | 'openai' | 'anthropic') {
    const vaultKeys = useStore((s) => s.keys);
    const legacy = provider === 'gemini' ? localStorage.getItem('aeonnimbus_terminal_gemini') : null;
    return vaultKeys?.[provider] || legacy || '';
}

/** Small status row shown wherever a tab needs a key: either confirms the
 * vault is supplying it, or offers a one-click way to open the vault. */
export function VaultKeyStatus({ provider, label }: { provider: 'gemini' | 'openai' | 'anthropic'; label: string }) {
    const key = useVaultKey(provider);
    const setView = useStore((s) => s.setView);
    const setActiveTab = useStore((s) => s.setActiveTab);
    const openVault = () => { setActiveTab('research'); setView('setup'); };
    if (key) {
        return <span className="badge-success text-[10px]">🔑 {label} key from vault</span>;
    }
    return (
        <button onClick={openVault} className="badge-gold text-[10px] cursor-pointer">
            🔑 Add {label} key in Vault →
        </button>
    );
}

/** Turn raw LLM provider errors into a human sentence. */
export function humanizeErr(e: string): string {
    if (/PerDay|LLM_QUOTA|quotaValue/i.test(e)) {
        return '🚫 Gemini free-tier DAILY quota exhausted (~20 requests/day per model on your key). ' +
            'It resets at midnight Pacific. Options: use a paid Gemini key, a different key, ' +
            'or switch provider below (OpenAI / Anthropic).';
    }
    if (/429|RESOURCE_EXHAUSTED/i.test(e)) {
        return '⏳ Rate limit hit (requests per minute). Wait ~1 minute and try again.';
    }
    if (/401|403|API key not valid|invalid|400 Client Error.*generativelanguage/i.test(e)) {
        return '🔑 The API key was rejected — double-check it.';
    }
    return e;
}

export function ErrorNote({ msg }: { msg: string }) {
    return <p className="mt-3 max-w-2xl text-sm leading-relaxed text-rose">{humanizeErr(msg)}</p>;
}

/** Progress bar with label — used by long-running agent jobs. */
export function ProgressBar({ pct, label, sub }: { pct: number; label: string; sub?: string }) {
    return (
        <div className="mt-4 card-cyan p-4">
            <div className="mb-2 flex items-center justify-between">
                <p className="text-sm text-white/80">{label}</p>
                <span className="font-mono text-xs text-accent">{Math.round(pct)}%</span>
            </div>
            <div className="score-bar">
                <div className="score-bar-fill" style={{ width: `${Math.min(pct, 100)}%` }} />
            </div>
            {sub && <p className="mt-2 text-xs text-white/40">{sub}</p>}
        </div>
    );
}

export function SourceBadge({ id, label: labelOverride }: { id: string; label?: string }) {
    const src = getSource(id);
    const real = src?.real ?? true;
    const label = labelOverride ?? src?.label ?? id;
    return <span className={real ? 'badge-accent' : 'badge-gold'}>{real ? `⚡ ${label}` : label}</span>;
}

function cap(n: number | null | undefined) {
    if (!n) return '—';
    if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
    return `$${(n / 1e6).toFixed(0)}M`;
}

/* ─── Types shared across tabs ───────────────────────────────────── */
type ObbQuote = {
    symbol: string; name: string | null; last_price: number | null;
    change_percent: number | null; market_cap: number | null;
    pe_ratio: number | null; year_high: number | null; year_low: number | null;
    ma_50d: number | null; ma_200d: number | null;
};
type MC = { spot: number; expected: number; probUp: number; annualVol: number; percentiles: Record<string, number> };
type DCF = { scenarios: Record<string, { growth: number; fairValue: number; upside: number }> };
type Personas = { mode: string; analyses: { persona: string; text: string }[] };

/* ─── Overview — one screen, every engine ────────────────────────── */
export function OverviewTab({ goTo }: { goTo: (tab: string) => void }) {
    const { ticker, recent, setTicker } = useStore();
    const [q, setQ] = useState<ObbQuote | null>(null);
    const [mc, setMc] = useState<MC | null>(null);
    const [dcf, setDcf] = useState<DCF | null>(null);
    const [per, setPer] = useState<Personas | null>(null);
    const [hist, setHist] = useState<{ date: string; close: number }[]>([]);
    const [err, setErr] = useState('');

    useEffect(() => {
        setQ(null); setMc(null); setDcf(null); setPer(null); setHist([]); setErr('');
        // OpenBB for price/MAs + Aeon fetcher for Δ%/cap/P-E (OpenBB's yfinance
        // provider leaves those null) — cross-source merge.
        Promise.all([
            jget<{ results: ObbQuote[] }>(`${OPENBB}/api/v1/equity/price/quote?provider=yfinance&symbol=${ticker}`)
                .then((d) => d.results[0]).catch(() => null),
            jget<{ name: string; price: number; changePercent: number | null; marketCap: number | null; pe: number | null; high52: number | null; low52: number | null }>(
                `${AEON}/market/quote/${ticker}`).catch(() => null),
        ]).then(([o, a]) => {
            if (!o && !a) { setErr('Quote unavailable from both OpenBB and Aeon'); return; }
            setQ({
                symbol: ticker,
                name: o?.name ?? a?.name ?? null,
                last_price: o?.last_price ?? a?.price ?? null,
                change_percent: o?.change_percent ?? (a?.changePercent != null ? a.changePercent / 100 : null),
                market_cap: o?.market_cap ?? a?.marketCap ?? null,
                pe_ratio: o?.pe_ratio ?? a?.pe ?? null,
                year_high: o?.year_high ?? a?.high52 ?? null,
                year_low: o?.year_low ?? a?.low52 ?? null,
                ma_50d: o?.ma_50d ?? null,
                ma_200d: o?.ma_200d ?? null,
            });
        });
        jget<MC>(`${AEON}/quant/montecarlo/${ticker}`).then(setMc).catch(() => {});
        jget<DCF>(`${AEON}/quant/dcf/${ticker}`).then(setDcf).catch(() => {});
        jpost<Personas>(`${AEON}/agents/personas`, { ticker, personas: ['buffett', 'lynch'] })
            .then(setPer).catch(() => {});
        jget<{ candles: { date: string; close: number }[] }>(`${AEON}/market/history/${ticker}?period=6mo`)
            .then((d) => setHist(d.candles)).catch(() => {});
    }, [ticker]);

    const pctPos = q?.last_price && q.year_low && q.year_high
        ? Math.round(100 * (q.last_price - q.year_low) / (q.year_high - q.year_low)) : null;

    return (
        <div className="animate-fade-in space-y-4">
            {/* Header strip — OpenBB live quote */}
            <div className="card-cyan p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                    <div>
                        <span className="font-display text-3xl font-black text-gradient">{ticker}</span>
                        <span className="ml-3 text-white/50">{q?.name ?? '…'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        {recent.length > 0 && recent.map((r) => (
                            <button key={r} onClick={() => setTicker(r)}
                                className="badge cursor-pointer border border-white/10 font-mono text-white/40 transition hover:border-accent/40 hover:text-accent">
                                {r}
                            </button>
                        ))}
                        <SourceBadge id="market-data" label="Live" />
                    </div>
                </div>
                {q && (
                    <div className="mt-3 grid grid-cols-2 gap-3 font-mono text-sm sm:grid-cols-4 lg:grid-cols-6">
                        <div><p className="stat-label">Price</p><p className="text-xl font-bold text-white">${q.last_price}</p></div>
                        <div><p className="stat-label">Change</p><p className={`text-xl font-bold ${(q.change_percent ?? 0) >= 0 ? 'text-emerald' : 'text-rose'}`}>{q.change_percent == null ? '—' : `${(q.change_percent * 100).toFixed(2)}%`}</p></div>
                        <div><p className="stat-label">Mkt Cap</p><p className="text-xl font-bold text-white">{cap(q.market_cap)}</p></div>
                        <div><p className="stat-label">P/E</p><p className="text-xl font-bold text-white">{q.pe_ratio?.toFixed(1) ?? '—'}</p></div>
                        <div><p className="stat-label">MA50 / MA200</p><p className="text-sm pt-1 text-white/70">{q.ma_50d?.toFixed(0)} / {q.ma_200d?.toFixed(0)}</p></div>
                        <div><p className="stat-label">52W position</p><p className="text-xl font-bold text-accent">{pctPos == null ? '—' : `${pctPos}%`}</p></div>
                    </div>
                )}
                {q && pctPos != null && (
                    <div className="mt-3">
                        <div className="relative h-1.5 rounded-full bg-white/[0.06]">
                            <div className="absolute inset-y-0 left-0"
                                style={{ width: `${pctPos}%`, background: 'var(--gold)', borderRadius: 1 }} />
                            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
                                style={{ left: `${pctPos}%`, width: 8, height: 8, borderRadius: '50%', background: 'var(--gold2)', border: '2px solid var(--bg)' }} />
                        </div>
                        <div className="mt-1 flex justify-between font-mono text-[10px] text-white/30">
                            <span>52W low ${q.year_low}</span><span>52W high ${q.year_high}</span>
                        </div>
                    </div>
                )}
                {err && <ErrorNote msg={err} />}
                {hist.length > 5 && (
                    <div className="mt-4 h-40">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={hist} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                                <defs>
                                    <linearGradient id="aeonFill" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#D4AF37" stopOpacity={0.28} />
                                        <stop offset="100%" stopColor="#D4AF37" stopOpacity={0.00} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="date" hide />
                                <YAxis domain={['auto', 'auto']} hide />
                                <Tooltip contentStyle={{ backgroundColor: '#111114', border: '1px solid rgba(212,175,55,0.20)', borderRadius: '3px', fontSize: '11px', fontFamily: '"JetBrains Mono", monospace', color: '#E8E6DF' }}
                                    formatter={(v: number) => [`$${v}`, 'close']} />
                                <Area type="monotone" dataKey="close" stroke="#D4AF37" strokeWidth={1.5} fill="url(#aeonFill)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                {/* Quant snapshot */}
                <div className="card p-5">
                    <div className="mb-3 flex items-center justify-between">
                        <h3 className="section-heading">Quant Snapshot</h3>
                        <button className="text-xs text-accent hover:underline" onClick={() => goTo('quant')}>full lab →</button>
                    </div>
                    {mc ? (
                        <>
                            <p className="text-sm text-white/70">Monte Carlo 1Y: P(up) <span className="font-mono text-accent">{mc.probUp}%</span> · E[S] <span className="font-mono">${mc.expected}</span> · σ {mc.annualVol}%</p>
                            <div className="score-bar mt-2"><div className="score-bar-fill" style={{ width: `${mc.probUp}%` }} /></div>
                        </>
                    ) : <p className="text-sm text-white/30">computing…</p>}
                    {dcf && (
                        <div className="mt-4 flex justify-between font-mono text-sm">
                            {Object.entries(dcf.scenarios).map(([n, s]) => (
                                <div key={n} className="text-center">
                                    <p className="stat-label capitalize">{n}</p>
                                    <p className={s.upside >= 0 ? 'text-emerald' : 'text-rose'}>${s.fairValue}</p>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Persona quick takes */}
                <div className="card p-5">
                    <div className="mb-3 flex items-center justify-between">
                        <h3 className="section-heading">Investor Lenses</h3>
                        <button className="text-xs text-accent hover:underline" onClick={() => goTo('personas')}>all personas →</button>
                    </div>
                    {per ? per.analyses.map((a) => (
                        <p key={a.persona} className="mb-2 text-sm text-white/70">
                            <span className="capitalize text-nebula-light font-semibold">{a.persona}:</span> {a.text.slice(0, 140)}…
                        </p>
                    )) : <p className="text-sm text-white/30">thinking…</p>}
                </div>
            </div>

            {/* Deep engines — launch pads */}
            <div className="grid gap-4 sm:grid-cols-3">
                <button onClick={() => goTo('research')} className="card p-5 text-left transition hover:ring-cyan-glow">
                    <p className="font-display font-bold">🧠 Full Report</p>
                    <p className="mt-1 text-xs text-white/50">55-dimension Aeon report + PDF · ~10s</p>
                </button>
                <button onClick={() => goTo('agents')} className="card-premium p-5 text-left transition hover:ring-nebula-glow">
                    <p className="font-display font-bold">⚔️ Agent Debate</p>
                    <p className="mt-1 text-xs text-white/50">Multi-agent debate engine · 3–10 min · needs key</p>
                </button>
                <button onClick={() => goTo('analyst')} className="card p-5 text-left transition hover:ring-cyan-glow">
                    <p className="font-display font-bold">🔬 Deep Research</p>
                    <p className="mt-1 text-xs text-white/50">11-agent RAG system over SEC filings</p>
                </button>
            </div>
        </div>
    );
}

/* ─── Markets — REAL OpenBB Platform API ─────────────────────────── */
/** One tab, two engines: the live screener and the quant lab both work off
 * the terminal-wide ticker, so they now share a single "Markets" tab
 * instead of forcing a click to move between them. */
export function MarketsTab() {
    return (
        <div className="animate-fade-in space-y-4">
            <MarketsScreener />
            <QuantSection />
        </div>
    );
}

function MarketsScreener() {
    const { ticker } = useStore();
    const [rows, setRows] = useState<ObbQuote[]>([]);
    const [list, setList] = useState('AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,JPM');
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState('');

    const load = async (symbols: string) => {
        setBusy(true); setErr('');
        try {
            // OpenBB's yfinance provider leaves Δ%/cap/P-E null in batch quotes —
            // merge with the Aeon fetcher, which has exactly those fields.
            const [obb, aeon] = await Promise.all([
                jget<{ results: ObbQuote[] }>(
                    `${OPENBB}/api/v1/equity/price/quote?provider=yfinance&symbol=${encodeURIComponent(symbols)}`)
                    .then((d) => d.results).catch(() => [] as ObbQuote[]),
                jget<{ results: { ticker: string; changePercent: number | null; marketCap: number | null; pe: number | null; high52: number | null; low52: number | null; price: number | null; name: string | null }[] }>(
                    `${AEON}/market/screener?tickers=${encodeURIComponent(symbols)}`)
                    .then((d) => d.results).catch(() => []),
            ]);
            const fill = new Map(aeon.map((a) => [a.ticker, a]));
            const base: ObbQuote[] = obb.length ? obb : aeon.map((a) => ({
                symbol: a.ticker, name: a.name, last_price: a.price,
                change_percent: null, market_cap: null, pe_ratio: null,
                year_high: a.high52, year_low: a.low52, ma_50d: null, ma_200d: null,
            }));
            if (!base.length) throw new Error('no data from OpenBB or Aeon');
            setRows(base.map((r) => {
                const a = fill.get(r.symbol);
                return {
                    ...r,
                    change_percent: r.change_percent ?? (a?.changePercent != null ? a.changePercent / 100 : null),
                    market_cap: r.market_cap ?? a?.marketCap ?? null,
                    pe_ratio: r.pe_ratio ?? a?.pe ?? null,
                    year_high: r.year_high ?? a?.high52 ?? null,
                    year_low: r.year_low ?? a?.low52 ?? null,
                };
            }));
        } catch (e) { setErr(`Market data unavailable: ${e}`); }
        setBusy(false);
    };

    useEffect(() => {
        const syms = list.includes(ticker) ? list : `${ticker},${list}`;
        setList(syms); load(syms);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [ticker]);

    return (
        <div className="animate-fade-in card p-5">
            <div className="mb-3 flex items-center gap-3">
                <h2 className="section-heading">Markets</h2>
                <SourceBadge id="market-data" />
            </div>
            <form className="mb-4 flex gap-2" onSubmit={(e) => { e.preventDefault(); load(list); }}>
                <input className="input-field" value={list} onChange={(e) => setList(e.target.value)} />
                <button className="btn-primary whitespace-nowrap" disabled={busy}>{busy ? 'Loading…' : 'Refresh'}</button>
            </form>
            {err && <ErrorNote msg={err} />}
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-white/[0.06] text-left text-[10px] uppercase tracking-wider text-white/40">
                            <th className="px-3 py-2">Symbol</th><th className="px-3 py-2">Price</th>
                            <th className="px-3 py-2">Δ%</th><th className="px-3 py-2">Mkt Cap</th>
                            <th className="px-3 py-2">P/E</th><th className="px-3 py-2">MA50</th>
                            <th className="px-3 py-2">MA200</th><th className="px-3 py-2">52W Range</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows.map((r) => (
                            <tr key={r.symbol} className={`border-b border-white/[0.03] ${r.symbol === ticker ? 'bg-accent/[0.06]' : ''}`}>
                                <td className="px-3 py-2 font-mono font-bold text-accent cursor-pointer"
                                    onClick={() => useStore.getState().setTicker(r.symbol)}>{r.symbol}</td>
                                <td className="px-3 py-2 font-mono">{r.last_price ?? '—'}</td>
                                <td className={`px-3 py-2 font-mono ${(r.change_percent ?? 0) >= 0 ? 'text-emerald' : 'text-rose'}`}>
                                    {r.change_percent == null ? '—' : `${(r.change_percent * 100).toFixed(2)}%`}
                                </td>
                                <td className="px-3 py-2 font-mono">{cap(r.market_cap)}</td>
                                <td className="px-3 py-2 font-mono">{r.pe_ratio?.toFixed(1) ?? '—'}</td>
                                <td className="px-3 py-2 font-mono text-white/60">{r.ma_50d?.toFixed(1) ?? '—'}</td>
                                <td className="px-3 py-2 font-mono text-white/60">{r.ma_200d?.toFixed(1) ?? '—'}</td>
                                <td className="px-3 py-2 font-mono text-white/50">{r.year_low} – {r.year_high}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <p className="mt-3 text-xs text-white/30">
                Click a symbol to make it the terminal-wide ticker.
            </p>
        </div>
    );
}

/* ─── Agent Desk — REAL TradingAgents (manual launch: costs tokens) ─ */
type TaJob = { status: 'running' | 'done' | 'error'; decision?: string; error?: string; report?: Record<string, string | null> };

const REPORT_LABELS: [string, string][] = [
    ['marketReport', '📈 Market Analyst'],
    ['sentimentReport', '💬 Sentiment Analyst'],
    ['newsReport', '📰 News Analyst'],
    ['fundamentalsReport', '🏦 Fundamentals Analyst'],
    ['investmentPlan', '⚖️ Research Judge (Bull vs Bear)'],
    ['traderPlan', '⚡ Trader Plan'],
    ['finalDecision', '🛡️ Risk Management — Final Decision'],
];

// Estimated stage timeline for a TradingAgents run (~6 min typical).
// The graph exposes no live progress, so this is elapsed-time based.
const TA_EST_TOTAL = 360; // seconds
const TA_STAGES: [number, string][] = [
    [0.14, '📈 Market analyst gathering technicals'],
    [0.28, '💬 Sentiment analyst reading social data'],
    [0.42, '📰 News analyst scanning headlines'],
    [0.56, '🏦 Fundamentals analyst reviewing financials'],
    [0.74, '⚖️ Bull vs Bear researchers debating'],
    [0.86, '⚡ Trader drafting the plan'],
    [1.00, '🛡️ Risk team reviewing the final call'],
];

const PROVIDERS = [
    ['google', 'Gemini'], ['openai', 'OpenAI'], ['anthropic', 'Anthropic'],
] as const;

const PROVIDER_TO_VAULT: Record<string, 'gemini' | 'openai' | 'anthropic'> = {
    google: 'gemini', openai: 'openai', anthropic: 'anthropic',
};

/** One tab, two kinds of AI judgment: the fast free persona take and the
 * slow deep multi-agent debate now live on the same "Agents" tab, quick
 * take on top since it's the one that auto-loads. */
export function AgentDeskTab() {
    return (
        <div className="animate-fade-in space-y-4">
            <PersonasSection />
            <AgentDebateSection />
        </div>
    );
}

function AgentDebateSection() {
    const { ticker } = useStore();
    const [provider, setProvider] = useState<string>(() => localStorage.getItem('aeonnimbus_ta_provider') || 'google');
    const key = useVaultKey(PROVIDER_TO_VAULT[provider]);
    const [job, setJob] = useState<TaJob | null>(null);
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState('');
    const [elapsed, setElapsed] = useState(0);
    const timer = useRef<ReturnType<typeof setInterval> | null>(null);

    const poll = (jobId: string) => {
        if (timer.current) clearInterval(timer.current);
        timer.current = setInterval(async () => {
            setElapsed((s) => s + 5);
            try {
                const j = await jget<TaJob>(`${TA}/job/${jobId}`);
                setJob(j);
                if (j.status !== 'running') {
                    if (timer.current) clearInterval(timer.current);
                    setBusy(false);
                    localStorage.removeItem('aeonnimbus_ta_job');
                }
            } catch { /* keep polling */ }
        }, 5000);
    };

    const run = async () => {
        if (!key) { setErr(`TradingAgents needs a real ${PROVIDERS.find(([p]) => p === provider)?.[1]} API key.`); return; }
        localStorage.setItem('aeonnimbus_ta_provider', provider);
        setBusy(true); setErr(''); setJob(null); setElapsed(0);
        try {
            const { jobId } = await jpost<{ jobId: string }>(`${TA}/run`, { ticker, provider, apiKey: key });
            localStorage.setItem('aeonnimbus_ta_job', jobId);   // survive tab switches
            poll(jobId);
        } catch (e) { setErr(String(e)); setBusy(false); }
    };

    // Resume a run that was started before a tab switch or reload
    useEffect(() => {
        const pending = localStorage.getItem('aeonnimbus_ta_job');
        if (pending) { setBusy(true); poll(pending); }
        return () => { if (timer.current) clearInterval(timer.current); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="animate-fade-in card p-5">
            <div className="mb-1 flex items-center gap-3">
                <h2 className="section-heading">Agent Desk · {ticker}</h2>
                <SourceBadge id="multi-agent" />
            </div>
            <p className="mb-3 text-xs text-white/40">
                4 analysts → bull/bear debate → trader → risk team. 3–10 min, real token usage. Uses the terminal-wide ticker.
            </p>
            <div className="flex flex-wrap items-center gap-2">
                <button className="btn-primary" onClick={run} disabled={busy}>
                    {busy ? `Running… ${Math.floor(elapsed / 60)}m ${elapsed % 60}s` : `Run full debate on ${ticker}`}
                </button>
                <select className="input-field max-w-[130px]" value={provider}
                    onChange={(e) => setProvider(e.target.value)} disabled={busy}>
                    {PROVIDERS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
                <VaultKeyStatus provider={PROVIDER_TO_VAULT[provider]} label={PROVIDERS.find(([p]) => p === provider)?.[1] ?? ''} />
            </div>
            {err && <ErrorNote msg={err} />}
            {busy && (() => {
                const frac = Math.min(elapsed / TA_EST_TOTAL, 0.97);
                const stage = TA_STAGES.find(([end]) => frac <= end) ?? TA_STAGES[TA_STAGES.length - 1];
                return (
                    <ProgressBar
                        pct={frac * 100}
                        label={stage[1]}
                        sub={`Estimated timeline based on a typical ~6 min run — the graph itself doesn't stream progress. Elapsed ${Math.floor(elapsed / 60)}m ${elapsed % 60}s. Safe to switch tabs; the run resumes when you return.`}
                    />
                );
            })()}
            {job?.status === 'error' && <ErrorNote msg={job.error || 'unknown error'} />}
            {job?.status === 'done' && (
                <div className="mt-4 space-y-3">
                    <div className="card-premium p-4">
                        <p className="stat-label mb-1 text-accent">FINAL DECISION</p>
                        <p className="font-display text-2xl font-bold text-gradient">{job.decision}</p>
                    </div>
                    {REPORT_LABELS.map(([k, label]) => job.report?.[k] && (
                        <details key={k} className="card-glass p-4">
                            <summary className="cursor-pointer stat-label">{label}</summary>
                            <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-white/80">{job.report[k]}</p>
                        </details>
                    ))}
                </div>
            )}
        </div>
    );
}

/* ─── Quant Lab — auto-runs on the global ticker ─────────────────── */
type MK = { optimal: { weights: Record<string, number>; expectedReturn: number; volatility: number; sharpe: number } };

function QuantSection() {
    const { ticker } = useStore();
    const [mc, setMc] = useState<MC | null>(null);
    const [dcf, setDcf] = useState<DCF | null>(null);
    const [mk, setMk] = useState<MK | null>(null);
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState('');
    const [port, setPort] = useState('AAPL,MSFT,GOOGL,NVDA');

    useEffect(() => {
        setBusy(true); setErr(''); setMc(null); setDcf(null);
        Promise.all([jget<MC>(`${AEON}/quant/montecarlo/${ticker}`), jget<DCF>(`${AEON}/quant/dcf/${ticker}`)])
            .then(([m, d]) => { setMc(m); setDcf(d); })
            .catch((e) => setErr(String(e)))
            .finally(() => setBusy(false));
    }, [ticker]);

    const optimize = async () => {
        setBusy(true); setErr(''); setMk(null);
        try { setMk(await jget<MK>(`${AEON}/quant/markowitz?tickers=${encodeURIComponent(port)}`)); }
        catch (e) { setErr(String(e)); }
        setBusy(false);
    };

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <div className="mb-3 flex items-center gap-3">
                    <h2 className="section-heading">Quant · {ticker}</h2>
                    <SourceBadge id="quant-native" />
                    {busy && <span className="text-xs text-white/40">computing…</span>}
                </div>
                {err && <ErrorNote msg={err} />}
                {mc && (
                    <div className="grid gap-4 sm:grid-cols-2">
                        <div className="card-cyan p-4">
                            <p className="stat-label mb-2">Monte Carlo · 10K GBM paths · 1Y</p>
                            <p className="text-sm text-white/70">Spot ${mc.spot} → E[S] ${mc.expected} · P(up) <span className="font-mono text-accent">{mc.probUp}%</span> · σ {mc.annualVol}%</p>
                            <div className="mt-2 flex justify-between font-mono text-xs text-white/60">
                                {Object.entries(mc.percentiles).map(([k, v]) => <span key={k}>{k}: ${v}</span>)}
                            </div>
                        </div>
                        {dcf && (
                            <div className="card-premium p-4">
                                <p className="stat-label mb-2">DCF fair value · WACC 9%</p>
                                {Object.entries(dcf.scenarios).map(([n, s]) => (
                                    <div key={n} className="flex justify-between py-0.5 text-sm">
                                        <span className="capitalize text-white/60">{n} ({(s.growth * 100).toFixed(0)}% g)</span>
                                        <span className="font-mono">${s.fairValue} <span className={s.upside >= 0 ? 'text-emerald' : 'text-rose'}>({s.upside > 0 ? '+' : ''}{s.upside}%)</span></span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
            <div className="card p-5">
                <h2 className="section-heading mb-3">Markowitz Optimizer · max Sharpe</h2>
                <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); optimize(); }}>
                    <input className="input-field" value={port} onChange={(e) => setPort(e.target.value)} />
                    <button className="btn-nebula whitespace-nowrap" disabled={busy}>{busy ? 'Working…' : 'Optimize'}</button>
                </form>
                {mk && (
                    <div className="mt-4">
                        <div className="mb-3 flex flex-wrap gap-2">
                            {Object.entries(mk.optimal.weights).map(([s, w]) => <span key={s} className="badge-accent">{s} {w}%</span>)}
                        </div>
                        <p className="font-mono text-sm text-white/70">E[r] {mk.optimal.expectedReturn}% · σ {mk.optimal.volatility}% · Sharpe {mk.optimal.sharpe}</p>
                    </div>
                )}
            </div>
        </div>
    );
}

/* ─── Personas — auto-runs demo (free); live analysis is manual ──── */
const ALL_PERSONAS = [
    ['buffett', '🏛️ Buffett'], ['graham', '📚 Graham'], ['lynch', '🛒 Lynch'],
    ['munger', '🧠 Munger'], ['marks', '🌊 Marks'],
] as const;

function PersonasSection() {
    const { ticker } = useStore();
    const key = useVaultKey('gemini');
    const [sel, setSel] = useState<string[]>(['buffett', 'graham', 'lynch']);
    const [res, setRes] = useState<Personas | null>(null);
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState('');

    const toggle = (p: string) => setSel((s) => (s.includes(p) ? s.filter((x) => x !== p) : [...s, p]));
    const run = async (useKey: boolean) => {
        setBusy(true); setErr(''); setRes(null);
        try {
            setRes(await jpost<Personas>(`${AEON}/agents/personas`,
                { ticker, personas: sel, geminiKey: useKey && key ? key : null }));
        } catch (e) { setErr(String(e)); }
        setBusy(false);
    };

    // Free demo take auto-loads whenever the global ticker changes
    useEffect(() => { run(false); /* eslint-disable-next-line */ }, [ticker]);

    return (
        <div className="animate-fade-in card p-5">
            <div className="mb-1 flex items-center gap-3">
                <h2 className="section-heading">Personas · {ticker}</h2>
                <SourceBadge id="personas-native" />
            </div>
            <div className="my-3 flex flex-wrap gap-2">
                {ALL_PERSONAS.map(([id, label]) => (
                    <button key={id} onClick={() => toggle(id)}
                        className={sel.includes(id) ? 'badge-nebula cursor-pointer' : 'badge cursor-pointer border border-white/10 text-white/40'}>
                        {label}
                    </button>
                ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
                <button className="btn-primary" disabled={busy || !key} onClick={() => run(true)}>
                    {busy ? 'Analyzing…' : `Live AI analysis of ${ticker}`}
                </button>
                <VaultKeyStatus provider="gemini" label="Gemini" />
            </div>
            {err && <ErrorNote msg={err} />}
            {res && (
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {res.mode === 'demo' && <span className="badge-gold sm:col-span-2">Quick take (free) — button above runs live AI</span>}
                    {res.analyses.map((a) => (
                        <div key={a.persona} className="card-premium p-4">
                            <p className="stat-label mb-1 capitalize text-nebula-light">
                                {ALL_PERSONAS.find(([id]) => id === a.persona)?.[1] ?? a.persona}
                            </p>
                            <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/80">{a.text}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
