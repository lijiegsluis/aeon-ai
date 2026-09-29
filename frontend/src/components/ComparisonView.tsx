/**
 * Compare — up to 5 tickers side by side: growth of $100 over a chosen window,
 * return / risk stats, and the fundamentals snapshot.
 */
import { useEffect, useMemo, useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useStore } from '../store';
import { ErrorNote } from './Terminal';
import { ANALYTICS_URL } from '../config';
import { jget, jpost } from '../utils/api';

interface Quote {
    name?: string;
    price?: number;
    changePercent?: number;
    pe?: number;
    marketCap?: number;
    beta?: number;
    dividendYield?: number;
    error?: string;
}
type Stats = {
    ret1M: number | null;
    ret3M: number | null;
    ret6M: number | null;
    ret1Y: number | null;
    retYTD: number | null;
    vol: number | null;
    maxDrawdown: number | null;
};
type Perf = { tickers: string[]; missing: string[]; series: Record<string, number | string>[]; stats: Record<string, Stats> };

// Validated categorical order (dark surface): blue, orange, aqua, yellow, magenta.
// Only the first three separate against every pair, so lines 4–5 also get a dash.
const COLORS = ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181'];
const DASH = [undefined, undefined, undefined, '6 3', '2 3'];
const PERIODS = [
    ['3mo', '3M'],
    ['6mo', '6M'],
    ['1y', '1Y'],
    ['2y', '2Y'],
    ['5y', '5Y'],
] as const;

const pct = (v: number | null | undefined, signed = true) => (v == null ? '—' : `${signed && v > 0 ? '+' : ''}${v.toFixed(1)}%`);

export default function ComparisonView() {
    const globalTicker = useStore((s) => s.ticker);
    const setTicker = useStore((s) => s.setTicker);
    const [tickers, setTickers] = useState<string[]>(() => [...new Set([globalTicker, 'SPY'])]);
    const [input, setInput] = useState('');
    const [period, setPeriod] = useState<string>('1y');
    const [quotes, setQuotes] = useState<Record<string, Quote>>({});
    const [perf, setPerf] = useState<Perf | null>(null);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState('');

    const addTicker = () => {
        const add = input
            .split(/[\s,]+/)
            .map((t) => t.trim().toUpperCase())
            .filter(Boolean);
        setTickers((cur) => [...new Set([...cur, ...add])].slice(0, 5));
        setInput('');
    };

    useEffect(() => {
        if (!tickers.length) {
            setPerf(null);
            setQuotes({});
            return;
        }
        let cancelled = false;
        setLoading(true);
        setErr('');
        Promise.allSettled([
            jpost<{ comparison: Record<string, Quote> }>(`${ANALYTICS_URL}/api/compare`, { tickers }),
            jget<Perf>(`${ANALYTICS_URL}/market/compare?tickers=${encodeURIComponent(tickers.join(','))}&period=${period}`),
        ]).then(([q, p]) => {
            if (cancelled) return;
            setQuotes(q.status === 'fulfilled' ? q.value.comparison : {});
            setPerf(p.status === 'fulfilled' ? p.value : null);
            const errs = [q, p].filter((r): r is PromiseRejectedResult => r.status === 'rejected').map((r) => String(r.reason));
            setErr([...new Set(errs)].join(' · '));
            setLoading(false);
        });
        return () => {
            cancelled = true;
        };
    }, [tickers, period]);

    const colorOf = (t: string) => COLORS[tickers.indexOf(t) % COLORS.length];
    const lastPoint = perf?.series[perf.series.length - 1];
    const yDomain = useMemo(() => {
        if (!perf) return ['auto', 'auto'] as const;
        const vals = perf.series.flatMap((r) => perf.tickers.map((t) => r[t] as number)).filter((v) => typeof v === 'number');
        return [Math.floor(Math.min(...vals) / 10) * 10, Math.ceil(Math.max(...vals) / 10) * 10] as const;
    }, [perf]);

    const statRows: [keyof Stats, string, boolean][] = [
        ['ret1M', '1M return', true],
        ['ret3M', '3M return', true],
        ['retYTD', 'YTD return', true],
        ['ret1Y', '1Y return', true],
        ['vol', 'Volatility (ann.)', false],
        ['maxDrawdown', 'Max drawdown', true],
    ];
    const quoteRows: [keyof Quote, string, (v: number) => string][] = [
        ['price', 'Price', (v) => `$${v.toFixed(2)}`],
        ['changePercent', 'Day change', (v) => `${v > 0 ? '+' : ''}${v.toFixed(2)}%`],
        ['pe', 'P/E', (v) => v.toFixed(1)],
        ['marketCap', 'Market cap', (v) => (v >= 1e12 ? `$${(v / 1e12).toFixed(2)}T` : `$${(v / 1e9).toFixed(1)}B`)],
        ['beta', 'Beta', (v) => v.toFixed(2)],
        ['dividendYield', 'Dividend yield', (v) => `${(v * 100).toFixed(2)}%`],
    ];

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <h2 className="section-heading mb-4">Compare</h2>
                <form
                    className="mb-3 flex gap-2"
                    onSubmit={(e) => {
                        e.preventDefault();
                        addTicker();
                    }}
                >
                    <input
                        className="input-field flex-1"
                        placeholder={tickers.length >= 5 ? 'Maximum 5 tickers' : 'Add tickers, e.g. MSFT NVDA'}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={tickers.length >= 5}
                    />
                    <button className="btn-primary" type="submit" disabled={tickers.length >= 5}>
                        Add
                    </button>
                </form>
                <div className="flex flex-wrap items-center gap-2">
                    {tickers.map((t) => (
                        <span key={t} className="badge flex items-center gap-2 border border-white/10 font-mono">
                            <i style={{ width: 10, height: 3, background: colorOf(t), display: 'inline-block', borderRadius: 2 }} />
                            {t}
                            <button aria-label={`Remove ${t}`} onClick={() => setTickers(tickers.filter((x) => x !== t))}>
                                ✕
                            </button>
                        </span>
                    ))}
                    <span className="ml-auto flex gap-1">
                        {PERIODS.map(([id, label]) => (
                            <button
                                key={id}
                                onClick={() => setPeriod(id)}
                                className={period === id ? 'badge-gold' : 'badge border border-white/10 text-white/50'}
                            >
                                {label}
                            </button>
                        ))}
                    </span>
                </div>
                {err && <ErrorNote msg={err} />}
            </div>

            {loading && !perf && <div className="text-center text-white/50">Loading comparison…</div>}

            {perf && perf.series.length > 1 && (
                <div className="card p-5">
                    <div className="mb-2 flex items-baseline justify-between gap-3">
                        <h3 className="section-heading">Growth of $100</h3>
                        <span className="text-xs text-white/40">
                            {String(perf.series[0].date)} → {String(lastPoint?.date)} · common trading days
                            {perf.missing.length > 0 && ` · no data: ${perf.missing.join(', ')}`}
                        </span>
                    </div>
                    <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={perf.series} margin={{ top: 8, right: 56, bottom: 0, left: 0 }}>
                                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                                    minTickGap={48}
                                    tickLine={false}
                                />
                                <YAxis
                                    domain={yDomain as unknown as [number, number]}
                                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                                    tickFormatter={(v) => `$${v}`}
                                    width={48}
                                    axisLine={false}
                                    tickLine={false}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#111114',
                                        border: '1px solid rgba(212,175,55,0.20)',
                                        borderRadius: 3,
                                        fontSize: 11,
                                        fontFamily: '"JetBrains Mono", monospace',
                                    }}
                                    labelStyle={{ color: '#E8E6DF' }}
                                    itemStyle={{ color: '#E8E6DF' }}
                                    formatter={(v: number, name: string) => [`$${v.toFixed(2)}`, name]}
                                />
                                <Legend wrapperStyle={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }} />
                                {perf.tickers.map((t) => (
                                    <Line
                                        key={t}
                                        dataKey={t}
                                        stroke={colorOf(t)}
                                        strokeWidth={2}
                                        strokeDasharray={DASH[tickers.indexOf(t)]}
                                        dot={false}
                                        isAnimationActive={false}
                                        label={(p: { index: number; x: number; y: number }) =>
                                            p.index === perf.series.length - 1 ? (
                                                <text key={`l${t}`} x={p.x + 6} y={p.y + 3} fontSize={10} fill="rgba(255,255,255,0.8)">
                                                    {t}
                                                </text>
                                            ) : (
                                                <g key={`l${t}${p.index}`} />
                                            )
                                        }
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {tickers.length > 0 && (perf || Object.keys(quotes).length > 0) && (
                <div className="card overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                                <th className="px-4 py-3 text-left text-white/50">Metric</th>
                                {tickers.map((t) => (
                                    <th key={t} className="px-4 py-3 text-left">
                                        <button
                                            className="font-bold text-gold"
                                            onClick={() => setTicker(t)}
                                            title={`Make ${t} the terminal ticker`}
                                        >
                                            {t}
                                        </button>
                                        <div className="text-xs font-normal text-white/50">{quotes[t]?.name}</div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {perf &&
                                statRows.map(([k, label, signed]) => (
                                    <tr key={k} className="border-b border-white/[0.03]">
                                        <td className="px-4 py-2.5 text-white/60">{label}</td>
                                        {tickers.map((t) => {
                                            const v = perf.stats[t]?.[k];
                                            const tone =
                                                signed && v != null && k !== 'maxDrawdown' ? (v >= 0 ? 'text-emerald' : 'text-rose') : '';
                                            return (
                                                <td key={t} className={`px-4 py-2.5 font-mono ${tone}`}>
                                                    {pct(v, signed && k !== 'maxDrawdown')}
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            {quoteRows.map(([k, label, fmt]) => (
                                <tr key={k} className="border-b border-white/[0.03]">
                                    <td className="px-4 py-2.5 text-white/60">{label}</td>
                                    {tickers.map((t) => {
                                        const v = quotes[t]?.[k];
                                        return (
                                            <td key={t} className="px-4 py-2.5 font-mono">
                                                {typeof v === 'number' ? (
                                                    fmt(v)
                                                ) : quotes[t]?.error && k === 'price' ? (
                                                    <span className="text-rose/70">n/a</span>
                                                ) : (
                                                    '—'
                                                )}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
