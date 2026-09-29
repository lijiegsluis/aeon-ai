/**
 * Aeon native deep dive — performance vs the S&P 500, risk, technicals, analyst
 * view, earnings track record and insider activity from Aeon's own analytics.
 * Needs no optional engine, so Deep Research is useful even when the 11-agent
 * system isn't running.
 */
import { useEffect, useState } from 'react';
import { ANALYTICS_URL } from '../config';
import { jget } from '../utils/api';
import { ErrorNote } from './Terminal';

type Rets = Partial<Record<'ret1M' | 'ret3M' | 'ret6M' | 'ret1Y' | 'retYTD', number | null>>;
type Snapshot = {
    ticker: string;
    price: number;
    asOf: string;
    unavailable: Record<string, string>;
    performance: Rets & {
        vol: number | null;
        maxDrawdown: number | null;
        beta?: number | null;
        correlation?: number | null;
        relative?: Rets;
        benchmark?: Rets;
    };
    technicals: {
        ma50: number | null;
        ma200: number | null;
        aboveMa200: boolean | null;
        rsi14: number | null;
        high52: number | null;
        low52: number | null;
        fromHigh52: number | null;
    };
    profile?: { shortName?: string; sector?: string; industry?: string; marketCap?: number; country?: string };
    valuation?: Record<string, number | null>;
    analysts?: {
        recommendation?: string;
        mean?: number | null;
        count?: number;
        targetMean?: number | null;
        targetHigh?: number | null;
        targetLow?: number | null;
        targetUpside?: number | null;
    };
    earnings?: {
        next: { date: string; epsEstimate: number | null } | null;
        history: { date: string; epsEstimate: number | null; epsActual: number | null; surprisePct: number | null }[];
        beatRate: number | null;
    } | null;
    insiders?: {
        trades: { insider: string; position: string; type: string; value: number | null; date: string; text: string }[];
        buys: number;
        sells: number;
    } | null;
};

const pct = (v: number | null | undefined, signed = true) => (v == null ? '—' : `${signed && v > 0 ? '+' : ''}${v.toFixed(1)}%`);
const tone = (v: number | null | undefined) => (v == null ? '' : v >= 0 ? 'text-emerald' : 'text-rose');
const money = (n?: number | null) =>
    n == null
        ? '—'
        : n >= 1e12
          ? `$${(n / 1e12).toFixed(2)}T`
          : n >= 1e9
            ? `$${(n / 1e9).toFixed(1)}B`
            : n >= 1e6
              ? `$${(n / 1e6).toFixed(1)}M`
              : `$${Math.round(n).toLocaleString()}`;

function Row({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="flex items-baseline justify-between gap-3 border-b border-white/[0.03] py-1.5">
            <span className="text-xs text-white/45">{label}</span>
            <span className="font-mono text-sm text-white/85">{children}</span>
        </div>
    );
}

export default function NativeDeepDive({ ticker }: { ticker: string }) {
    const [d, setD] = useState<Snapshot | null>(null);
    const [err, setErr] = useState('');

    useEffect(() => {
        let cancelled = false;
        setD(null);
        setErr('');
        jget<Snapshot>(`${ANALYTICS_URL}/research/snapshot/${encodeURIComponent(ticker)}`)
            .then((x) => !cancelled && setD(x))
            .catch((e) => !cancelled && setErr(String(e)));
        return () => {
            cancelled = true;
        };
    }, [ticker]);

    if (err) return <ErrorNote msg={err} />;
    if (!d) return <p className="text-sm text-white/40">Building the {ticker} deep dive…</p>;

    const p = d.performance;
    const windows: [keyof Rets, string][] = [
        ['ret1M', '1M'],
        ['ret3M', '3M'],
        ['ret6M', '6M'],
        ['retYTD', 'YTD'],
        ['ret1Y', '1Y'],
    ];

    return (
        <div className="space-y-4">
            <div className="card-cyan p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                    <div>
                        <span className="font-display text-2xl font-black text-gradient">{d.ticker}</span>
                        <span className="ml-3 text-white/50">{d.profile?.shortName}</span>
                        {d.profile?.sector && (
                            <span className="ml-3 text-xs text-white/35">
                                {d.profile.sector} · {d.profile.industry}
                            </span>
                        )}
                    </div>
                    <span className="font-mono text-xl text-white">${d.price}</span>
                </div>
                <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-left text-[10px] uppercase tracking-wider text-white/40">
                                <th className="py-1 pr-4">Return</th>
                                {windows.map(([, l]) => (
                                    <th key={l} className="py-1 pr-4">
                                        {l}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="font-mono">
                            <tr>
                                <td className="py-1 pr-4 font-sans text-white/60">{d.ticker}</td>
                                {windows.map(([k]) => (
                                    <td key={k} className={`py-1 pr-4 ${tone(p[k])}`}>
                                        {pct(p[k])}
                                    </td>
                                ))}
                            </tr>
                            {p.benchmark && (
                                <tr>
                                    <td className="py-1 pr-4 font-sans text-white/40">S&amp;P 500 (SPY)</td>
                                    {windows.map(([k]) => (
                                        <td key={k} className="py-1 pr-4 text-white/50">
                                            {pct(p.benchmark?.[k])}
                                        </td>
                                    ))}
                                </tr>
                            )}
                            {p.relative && (
                                <tr>
                                    <td className="py-1 pr-4 font-sans text-white/60">vs S&amp;P</td>
                                    {windows.map(([k]) => (
                                        <td key={k} className={`py-1 pr-4 ${tone(p.relative?.[k])}`}>
                                            {pct(p.relative?.[k])}
                                        </td>
                                    ))}
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
                <div className="card p-5">
                    <h3 className="section-heading mb-2">Risk</h3>
                    <Row label="Volatility (ann.)">{pct(p.vol, false)}</Row>
                    <Row label="Max drawdown (2y)">{pct(p.maxDrawdown, false)}</Row>
                    <Row label="Beta vs S&P (1y)">{p.beta ?? '—'}</Row>
                    <Row label="Correlation vs S&P">{p.correlation ?? '—'}</Row>
                </div>
                <div className="card p-5">
                    <h3 className="section-heading mb-2">Technicals</h3>
                    <Row label="50-day average">{d.technicals.ma50 ?? '—'}</Row>
                    <Row label="200-day average">
                        {d.technicals.ma200 ?? '—'}
                        {d.technicals.aboveMa200 != null && (
                            <span className={d.technicals.aboveMa200 ? 'ml-2 text-emerald' : 'ml-2 text-rose'}>
                                {d.technicals.aboveMa200 ? 'above' : 'below'}
                            </span>
                        )}
                    </Row>
                    <Row label="RSI (14)">{d.technicals.rsi14 ?? '—'}</Row>
                    <Row label="From 52-week high">{pct(d.technicals.fromHigh52)}</Row>
                    <Row label="52-week range">
                        {d.technicals.low52} – {d.technicals.high52}
                    </Row>
                </div>
                <div className="card p-5">
                    <h3 className="section-heading mb-2">Street view</h3>
                    {d.analysts ? (
                        <>
                            <Row label="Consensus">
                                {d.analysts.recommendation?.replace('_', ' ') ?? '—'}
                                {d.analysts.count ? ` (${d.analysts.count})` : ''}
                            </Row>
                            <Row label="Mean target">
                                {d.analysts.targetMean != null ? `$${d.analysts.targetMean}` : '—'}{' '}
                                <span className={tone(d.analysts.targetUpside)}>{pct(d.analysts.targetUpside)}</span>
                            </Row>
                            <Row label="Target range">
                                {d.analysts.targetLow ?? '—'} – {d.analysts.targetHigh ?? '—'}
                            </Row>
                            <Row label="P/E · forward P/E">
                                {d.valuation?.pe ?? '—'} · {d.valuation?.forwardPe ?? '—'}
                            </Row>
                            <Row label="Market cap">{money(d.profile?.marketCap)}</Row>
                        </>
                    ) : (
                        <p className="text-xs text-white/40">{d.unavailable.fundamentals ?? 'No analyst data.'}</p>
                    )}
                </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                <div className="card p-5">
                    <h3 className="section-heading mb-2">Earnings</h3>
                    {d.earnings ? (
                        <>
                            <p className="mb-2 text-sm text-white/70">
                                {d.earnings.next ? `Next report ${d.earnings.next.date}` : 'Next report date not announced'}
                                {d.earnings.next?.epsEstimate != null && ` · EPS est. ${d.earnings.next.epsEstimate}`}
                                {d.earnings.beatRate != null && ` · beat ${d.earnings.beatRate}% of the last ${d.earnings.history.length}`}
                            </p>
                            <table className="w-full text-sm">
                                <tbody className="font-mono">
                                    {d.earnings.history.map((h) => (
                                        <tr key={h.date} className="border-t border-white/[0.03]">
                                            <td className="py-1 text-white/50">{h.date}</td>
                                            <td className="py-1">est {h.epsEstimate ?? '—'}</td>
                                            <td className="py-1">act {h.epsActual ?? '—'}</td>
                                            <td className={`py-1 ${tone(h.surprisePct)}`}>{pct(h.surprisePct)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </>
                    ) : (
                        <p className="text-xs text-white/40">{d.unavailable.earnings}</p>
                    )}
                </div>
                <div className="card p-5">
                    <h3 className="section-heading mb-2">Insider activity</h3>
                    {d.insiders ? (
                        d.insiders.trades.length ? (
                            <>
                                <p className="mb-2 text-sm text-white/70">
                                    {d.insiders.buys} buys · {d.insiders.sells} sales in the latest filings
                                </p>
                                <table className="w-full text-sm">
                                    <tbody>
                                        {d.insiders.trades.slice(0, 8).map((t, i) => (
                                            <tr key={i} className="border-t border-white/[0.03]">
                                                <td className="py-1 font-mono text-white/50">{t.date}</td>
                                                <td className="py-1 text-white/75">
                                                    {t.insider}
                                                    <span className="text-white/35"> · {t.position}</span>
                                                </td>
                                                <td
                                                    className={`py-1 ${t.type === 'BUY' ? 'text-emerald' : t.type === 'SELL' ? 'text-rose' : 'text-white/50'}`}
                                                >
                                                    {t.type}
                                                </td>
                                                <td className="py-1 font-mono">{money(t.value)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </>
                        ) : (
                            <p className="text-sm text-white/50">No recent insider transactions.</p>
                        )
                    ) : (
                        <p className="text-xs text-white/40">{d.unavailable.insiders}</p>
                    )}
                </div>
            </div>
            <p className="text-[10px] text-white/30">
                Aeon native analytics · as of {new Date(d.asOf).toLocaleString()} · price-based sections work on any data source; street
                view, earnings and insiders need Yahoo fundamentals.
            </p>
        </div>
    );
}
