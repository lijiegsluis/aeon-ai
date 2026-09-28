/**
 * Analysis History & Replay
 * View past analyses and replay them
 */
import { useState, useEffect } from 'react';
import { useStore } from '../store';

interface HistoryItem {
    id: number;
    ticker: string;
    created_at: string;
    result_json: string;
}

export default function AnalysisHistory() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [filter, setFilter] = useState('');

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const res = await fetch('http://127.0.0.1:8000/api/analyses/history?user_id=1&limit=100');
            const data = await res.json();
            setHistory(data.history);
        } catch (e) {
            console.error('Failed to load history:', e);
        }
    };

    const replayAnalysis = async (id: number) => {
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/analyses/${id}`);
            const data = await res.json();
            // Load into store
            useStore.setState({ result: data.result, view: 'report' });
        } catch (e) {
            console.error('Failed to replay:', e);
        }
    };

    const filteredHistory = filter
        ? history.filter(h => h.ticker.toLowerCase().includes(filter.toLowerCase()))
        : history;

    const groupedByTicker = filteredHistory.reduce((acc, item) => {
        if (!acc[item.ticker]) acc[item.ticker] = [];
        acc[item.ticker].push(item);
        return acc;
    }, {} as Record<string, HistoryItem[]>);

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <h2 className="section-heading mb-4">Analysis History</h2>
                <input
                    className="input-field"
                    placeholder="Filter by ticker..."
                    value={filter}
                    onChange={e => setFilter(e.target.value)}
                />
            </div>

            {Object.keys(groupedByTicker).length === 0 && (
                <div className="card p-8 text-center text-white/50">
                    No analysis history yet. Run an analysis to save it.
                </div>
            )}

            {Object.entries(groupedByTicker).map(([ticker, items]) => (
                <div key={ticker} className="card">
                    <div className="p-4 border-b border-white/[0.06] flex items-center justify-between">
                        <div>
                            <h3 className="font-bold text-lg text-gold">{ticker}</h3>
                            <div className="text-xs text-white/50">{items.length} analyses</div>
                        </div>
                    </div>
                    <div className="divide-y divide-white/[0.03]">
                        {items.map(item => (
                            <div key={item.id} className="p-4 flex items-center justify-between hover:bg-white/[0.02]">
                                <div>
                                    <div className="text-sm text-white/70">
                                        {new Date(item.created_at).toLocaleString()}
                                    </div>
                                </div>
                                <button
                                    className="btn-ghost text-sm"
                                    onClick={() => replayAnalysis(item.id)}
                                >
                                    Replay
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}
