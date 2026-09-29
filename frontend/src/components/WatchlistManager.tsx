/**
 * Watchlist Manager with bulk analysis
 */
import { useState, useEffect } from 'react';
import { ErrorNote } from './Terminal';
import { ANALYTICS_URL } from '../config';

interface Watchlist {
    id: number;
    name: string;
    tickers: string[];
    created_at: string;
}

interface BulkResult {
    ticker: string;
    status: string;
    data?: any;
    error?: string;
}

export default function WatchlistManager() {
    const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
    const [name, setName] = useState('');
    const [tickers, setTickers] = useState('');
    const [analyzing, setAnalyzing] = useState<number | null>(null);
    const [bulkResults, setBulkResults] = useState<BulkResult[]>([]);
    const [err, setErr] = useState('');

    useEffect(() => {
        loadWatchlists();
    }, []);

    const loadWatchlists = async () => {
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/watchlists?user_id=1`);
            const data = await res.json();
            setWatchlists(data.watchlists);
            setErr('');
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
        }
    };

    const createWatchlist = async () => {
        const tickerList = tickers
            .split(',')
            .map((t) => t.trim().toUpperCase())
            .filter(Boolean);
        if (!name || tickerList.length === 0) return;

        try {
            const res = await fetch(`${ANALYTICS_URL}/api/watchlists`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, tickers: tickerList, user_id: 1 }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            setName('');
            setTickers('');
            setErr('');
            loadWatchlists();
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
        }
    };

    const analyzeWatchlist = async (id: number) => {
        setAnalyzing(id);
        setBulkResults([]);
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/watchlists/${id}/analyze`, { method: 'POST' });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            const data = await res.json();
            setBulkResults(data.results);
            setErr('');
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
        }
        setAnalyzing(null);
    };

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <h2 className="section-heading mb-4">Watchlists</h2>
                <div className="space-y-3">
                    <input className="input-field" placeholder="Watchlist name" value={name} onChange={(e) => setName(e.target.value)} />
                    <textarea
                        className="input-field"
                        placeholder="Tickers (comma-separated): AAPL, MSFT, GOOGL"
                        value={tickers}
                        onChange={(e) => setTickers(e.target.value)}
                        rows={3}
                    />
                    <button className="btn-primary" onClick={createWatchlist}>
                        Create Watchlist
                    </button>
                </div>
                {err && <ErrorNote msg={err} />}
            </div>

            {watchlists.map((wl) => (
                <div key={wl.id} className="card">
                    <div className="p-4 border-b border-white/[0.06]">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="font-bold text-gold">{wl.name}</h3>
                            <button className="btn-primary text-sm" onClick={() => analyzeWatchlist(wl.id)} disabled={analyzing === wl.id}>
                                {analyzing === wl.id ? 'Analyzing...' : 'Analyze All'}
                            </button>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                            {wl.tickers.map((t) => (
                                <span key={t} className="badge-accent text-xs">
                                    {t}
                                </span>
                            ))}
                        </div>
                    </div>
                    {analyzing === wl.id && bulkResults.length > 0 && (
                        <div className="p-4">
                            <div className="space-y-2">
                                {bulkResults.map((r) => (
                                    <div key={r.ticker} className="flex items-center justify-between text-sm">
                                        <span className="font-mono">{r.ticker}</span>
                                        {r.status === 'success' ? (
                                            <span className="text-emerald">
                                                ${r.data?.price} ({r.data?.changePercent > 0 ? '+' : ''}
                                                {r.data?.changePercent?.toFixed(2)}%)
                                            </span>
                                        ) : (
                                            <span className="text-rose">Error</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
