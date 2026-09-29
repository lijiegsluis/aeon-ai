/**
 * Watchlists — named ticker lists with a one-click quote sweep.
 */
import { useEffect, useState } from 'react';
import { ErrorNote } from './Terminal';
import { ANALYTICS_URL } from '../config';
import { useStore } from '../store';
import { jdelete, jget, jpost } from '../utils/api';

interface Watchlist {
    id: number;
    name: string;
    tickers: string[];
    created_at: string;
}

interface Quote {
    name?: string;
    price?: number;
    changePercent?: number | null;
    pe?: number | null;
    marketCap?: number | null;
}

interface BulkResult {
    ticker: string;
    status: 'success' | 'error';
    data?: Quote;
    error?: string;
}

const cap = (n?: number | null) =>
    !n ? '—' : n >= 1e12 ? `$${(n / 1e12).toFixed(2)}T` : n >= 1e9 ? `$${(n / 1e9).toFixed(1)}B` : `$${(n / 1e6).toFixed(0)}M`;

export default function WatchlistManager() {
    const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
    const [name, setName] = useState('');
    const [tickers, setTickers] = useState('');
    const [analyzing, setAnalyzing] = useState<number | null>(null);
    // Results stay on screen per watchlist after the sweep finishes.
    const [results, setResults] = useState<Record<number, BulkResult[]>>({});
    const [err, setErr] = useState('');
    const setTicker = useStore((s) => s.setTicker);
    const setActiveTab = useStore((s) => s.setActiveTab);

    const load = async () => {
        try {
            const data = await jget<{ watchlists: Watchlist[] }>(`${ANALYTICS_URL}/api/watchlists?user_id=1`);
            setWatchlists(data.watchlists);
            setErr('');
        } catch (e) {
            setErr(String(e));
        }
    };

    useEffect(() => {
        load();
    }, []);

    const create = async (e: React.FormEvent) => {
        e.preventDefault();
        const list = tickers
            .split(/[\s,]+/)
            .map((t) => t.trim().toUpperCase())
            .filter(Boolean);
        if (!name.trim() || list.length === 0) {
            setErr('Give the watchlist a name and at least one ticker.');
            return;
        }
        try {
            await jpost(`${ANALYTICS_URL}/api/watchlists`, { name, tickers: list, user_id: 1 });
            setName('');
            setTickers('');
            load();
        } catch (e) {
            setErr(String(e));
        }
    };

    const analyze = async (id: number) => {
        setAnalyzing(id);
        try {
            const data = await jpost<{ results: BulkResult[] }>(`${ANALYTICS_URL}/api/watchlists/${id}/analyze`, {});
            setResults((r) => ({ ...r, [id]: data.results }));
            setErr('');
        } catch (e) {
            setErr(String(e));
        }
        setAnalyzing(null);
    };

    const remove = async (id: number) => {
        try {
            await jdelete(`${ANALYTICS_URL}/api/watchlists/${id}`);
            setWatchlists((w) => w.filter((x) => x.id !== id));
        } catch (e) {
            setErr(String(e));
        }
    };

    const open = (t: string) => {
        setTicker(t);
        setActiveTab('overview');
    };

    return (
        <div className="animate-fade-in space-y-4">
            <form className="card p-5" onSubmit={create}>
                <h2 className="section-heading mb-4">Watchlists</h2>
                <div className="grid gap-3 md:grid-cols-[1fr_2fr_auto]">
                    <input
                        className="input-field"
                        placeholder="Name, e.g. AI leaders"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                    <input
                        className="input-field"
                        placeholder="Tickers: NVDA, AMD, AVGO"
                        value={tickers}
                        onChange={(e) => setTickers(e.target.value)}
                    />
                    <button className="btn-primary" type="submit">
                        Create
                    </button>
                </div>
                {err && <ErrorNote msg={err} />}
            </form>

            {watchlists.length === 0 && !err && <div className="card p-8 text-center text-white/50">No watchlists yet.</div>}

            {watchlists.map((wl) => {
                const res = results[wl.id];
                return (
                    <div key={wl.id} className="card">
                        <div className="border-b border-white/[0.06] p-4">
                            <div className="mb-2 flex items-center justify-between gap-3">
                                <h3 className="font-bold text-gold">{wl.name}</h3>
                                <div className="flex items-center gap-3">
                                    <button className="btn-primary text-sm" onClick={() => analyze(wl.id)} disabled={analyzing === wl.id}>
                                        {analyzing === wl.id ? 'Fetching quotes…' : res ? 'Refresh' : 'Analyze all'}
                                    </button>
                                    <button className="text-sm text-rose/70 hover:text-rose" onClick={() => remove(wl.id)}>
                                        Delete
                                    </button>
                                </div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {wl.tickers.map((t) => (
                                    <button
                                        key={t}
                                        className="badge-accent cursor-pointer text-xs"
                                        onClick={() => open(t)}
                                        title={`Open ${t}`}
                                    >
                                        {t}
                                    </button>
                                ))}
                            </div>
                        </div>
                        {res && (
                            <div className="overflow-x-auto p-4">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="text-left text-[10px] uppercase tracking-wider text-white/40">
                                            <th className="py-1 pr-3">Ticker</th>
                                            <th className="py-1 pr-3">Name</th>
                                            <th className="py-1 pr-3">Price</th>
                                            <th className="py-1 pr-3">Day</th>
                                            <th className="py-1 pr-3">P/E</th>
                                            <th className="py-1">Mkt cap</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {res.map((r) => (
                                            <tr key={r.ticker} className="border-t border-white/[0.03]">
                                                <td className="py-1.5 pr-3">
                                                    <button className="font-mono font-bold text-accent" onClick={() => open(r.ticker)}>
                                                        {r.ticker}
                                                    </button>
                                                </td>
                                                {r.status === 'success' && r.data ? (
                                                    <>
                                                        <td className="py-1.5 pr-3 text-white/60">{r.data.name ?? '—'}</td>
                                                        <td className="py-1.5 pr-3 font-mono">${r.data.price}</td>
                                                        <td
                                                            className={`py-1.5 pr-3 font-mono ${(r.data.changePercent ?? 0) >= 0 ? 'text-emerald' : 'text-rose'}`}
                                                        >
                                                            {r.data.changePercent == null
                                                                ? '—'
                                                                : `${r.data.changePercent > 0 ? '+' : ''}${r.data.changePercent.toFixed(2)}%`}
                                                        </td>
                                                        <td className="py-1.5 pr-3 font-mono">{r.data.pe?.toFixed(1) ?? '—'}</td>
                                                        <td className="py-1.5 font-mono">{cap(r.data.marketCap)}</td>
                                                    </>
                                                ) : (
                                                    <td colSpan={5} className="py-1.5 text-rose/80">
                                                        {r.error || 'unavailable'}
                                                    </td>
                                                )}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
