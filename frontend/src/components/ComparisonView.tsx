/**
 * Comparison view - side-by-side analysis of up to 5 tickers
 */
import { useState, useEffect } from 'react';
import { useStore } from '../store';
import { ErrorNote } from './Terminal';

interface CompareData {
    ticker: string;
    name?: string;
    price?: number;
    change?: number;
    changePercent?: number;
    pe?: number;
    marketCap?: number;
    beta?: number;
    dividendYield?: number;
    error?: string;
}

export default function ComparisonView() {
    const globalTicker = useStore(s => s.ticker);
    const [tickers, setTickers] = useState<string[]>([globalTicker]);
    const [input, setInput] = useState('');
    const [data, setData] = useState<CompareData[]>([]);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState('');

    const addTicker = () => {
        const t = input.trim().toUpperCase();
        if (t && !tickers.includes(t) && tickers.length < 5) {
            setTickers([...tickers, t]);
            setInput('');
        }
    };

    const removeTicker = (t: string) => {
        setTickers(tickers.filter(x => x !== t));
    };

    useEffect(() => {
        if (tickers.length === 0) return;
        setLoading(true);
        setErr('');
        fetch('http://127.0.0.1:8000/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tickers }),
        })
            .then(async r => {
                if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
                return r.json();
            })
            .then(d => setData(Object.entries(d.comparison).map(([ticker, data]: any) => ({ ticker, ...data }))))
            .catch((e) => { setData([]); setErr(String(e instanceof Error ? e.message : e)); })
            .finally(() => setLoading(false));
    }, [tickers]);

    const metrics = [
        { key: 'price', label: 'Price', format: (v: number) => `$${v.toFixed(2)}` },
        { key: 'changePercent', label: 'Change %', format: (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(2)}%` },
        { key: 'pe', label: 'P/E', format: (v: number) => v.toFixed(2) },
        { key: 'marketCap', label: 'Market Cap', format: (v: number) => `$${(v / 1e9).toFixed(2)}B` },
        { key: 'beta', label: 'Beta', format: (v: number) => v.toFixed(2) },
        { key: 'dividendYield', label: 'Div Yield', format: (v: number) => `${(v * 100).toFixed(2)}%` },
    ];

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <h2 className="section-heading mb-4">Compare Tickers</h2>
                <div className="flex gap-2 mb-4">
                    <input
                        className="input-field flex-1"
                        placeholder="Add ticker (max 5)"
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && addTicker()}
                        disabled={tickers.length >= 5}
                    />
                    <button className="btn-primary" onClick={addTicker} disabled={tickers.length >= 5}>
                        Add
                    </button>
                </div>
                <div className="flex gap-2 flex-wrap">
                    {tickers.map(t => (
                        <span key={t} className="badge-accent flex items-center gap-2">
                            {t}
                            <button onClick={() => removeTicker(t)} style={{ marginLeft: 4 }}>✕</button>
                        </span>
                    ))}
                </div>
            </div>

            {err && <ErrorNote msg={err} />}
            {loading && <div className="text-center text-white/50">Loading comparison...</div>}

            {!loading && data.length > 0 && (
                <div className="card overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                                <th className="px-4 py-3 text-left text-white/70">Metric</th>
                                {data.map(d => (
                                    <th key={d.ticker} className="px-4 py-3 text-left">
                                        <div className="font-bold text-gold">{d.ticker}</div>
                                        <div className="text-xs text-white/50 font-normal">{d.name}</div>
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {metrics.map(m => (
                                <tr key={m.key} className="border-b border-white/[0.03]">
                                    <td className="px-4 py-3 text-white/70">{m.label}</td>
                                    {data.map(d => {
                                        const val = (d as any)[m.key];
                                        const allVals = data.map(x => (x as any)[m.key]).filter(v => v != null);
                                        const isMax = val != null && val === Math.max(...allVals);
                                        const isMin = val != null && val === Math.min(...allVals);
                                        return (
                                            <td key={d.ticker} className="px-4 py-3 font-mono" style={{
                                                background: isMax ? 'rgba(0,255,100,0.1)' : isMin ? 'rgba(255,100,100,0.1)' : undefined,
                                            }}>
                                                {val != null ? m.format(val) : '—'}
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
