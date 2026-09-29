/**
 * Analysis History & Replay — every full Research report is saved; replay opens
 * it in the report viewer exactly as it was generated.
 */
import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { ANALYTICS_URL } from '../config';
import { jdelete, jget } from '../utils/api';
import { ErrorNote } from './Terminal';

interface HistoryItem {
    id: number;
    ticker: string;
    created_at: string;
    result_json: string;
}

type Summary = { grade?: string; score?: number; price?: number; empty: boolean };

function summarize(json: string): Summary {
    try {
        const r = JSON.parse(json);
        if (!r || !Object.keys(r).length) return { empty: true };
        return { grade: r.aeonScore?.grade, score: r.aeonScore?.numericScore, price: r.quote?.price ?? r.price, empty: false };
    } catch {
        return { empty: true };
    }
}

export default function AnalysisHistory() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [filter, setFilter] = useState('');
    const [err, setErr] = useState('');
    const setActiveTab = useStore((s) => s.setActiveTab);

    const loadHistory = async () => {
        try {
            const data = await jget<{ history: HistoryItem[] }>(`${ANALYTICS_URL}/api/analyses/history?user_id=1&limit=100`);
            setHistory(data.history);
            setErr('');
        } catch (e) {
            setErr(String(e));
        }
    };

    useEffect(() => {
        loadHistory();
    }, []);

    const replay = async (id: number) => {
        try {
            const data = await jget<{ result: unknown }>(`${ANALYTICS_URL}/api/analyses/${id}`);
            // The report viewer lives on the Research tab — switch there, or nothing shows.
            useStore.setState({ result: data.result as never, view: 'report', error: null });
            setActiveTab('research');
        } catch (e) {
            setErr(String(e));
        }
    };

    const remove = async (id: number) => {
        try {
            await jdelete(`${ANALYTICS_URL}/api/analyses/${id}`);
            setHistory((h) => h.filter((x) => x.id !== id));
        } catch (e) {
            setErr(String(e));
        }
    };

    const filtered = filter ? history.filter((h) => h.ticker.toLowerCase().includes(filter.toLowerCase())) : history;
    const grouped = filtered.reduce(
        (acc, item) => {
            (acc[item.ticker] ||= []).push(item);
            return acc;
        },
        {} as Record<string, HistoryItem[]>,
    );

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <h2 className="section-heading mb-4">Analysis History</h2>
                <input
                    className="input-field"
                    placeholder="Filter by ticker..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                />
                {err && <ErrorNote msg={err} />}
            </div>

            {Object.keys(grouped).length === 0 && !err && (
                <div className="card p-8 text-center text-white/50">
                    No saved reports yet. Every full report from the Research tab is saved here.
                </div>
            )}

            {Object.entries(grouped).map(([ticker, items]) => (
                <div key={ticker} className="card">
                    <div className="flex items-center justify-between border-b border-white/[0.06] p-4">
                        <div>
                            <h3 className="text-lg font-bold text-gold">{ticker}</h3>
                            <div className="text-xs text-white/50">
                                {items.length} report{items.length === 1 ? '' : 's'}
                            </div>
                        </div>
                    </div>
                    <div className="divide-y divide-white/[0.03]">
                        {items.map((item) => {
                            const s = summarize(item.result_json);
                            return (
                                <div key={item.id} className="flex items-center justify-between gap-3 p-4 hover:bg-white/[0.02]">
                                    <div className="text-sm text-white/70">
                                        {new Date(`${item.created_at.replace(' ', 'T')}Z`).toLocaleString()}
                                        {s.grade && (
                                            <span className="ml-3 font-mono text-gold">
                                                {s.grade}
                                                {s.score != null ? ` · ${s.score}/100` : ''}
                                            </span>
                                        )}
                                        {s.empty && <span className="ml-3 text-xs text-white/35">empty record</span>}
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <button className="btn-ghost text-sm" onClick={() => replay(item.id)} disabled={s.empty}>
                                            Replay
                                        </button>
                                        <button className="text-sm text-rose/70 hover:text-rose" onClick={() => remove(item.id)}>
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
}
