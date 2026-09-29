/**
 * Alerts tab — create and manage price / P-E alerts. The checking itself runs in
 * AlertsWatcher (mounted app-wide), so alerts fire on whatever tab is open.
 */
import { useEffect, useState } from 'react';
import { ErrorNote } from './Terminal';
import { ANALYTICS_URL } from '../config';
import { useStore } from '../store';
import { ALERTS_CHANGED, CONDITION_LABELS } from './AlertsWatcher';

interface Alert {
    id: number;
    ticker: string;
    condition_type: string;
    threshold: number;
    created_at: string;
    triggered_at?: string | null;
    triggered_value?: number | null;
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${ANALYTICS_URL}${path}`, init);
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = Array.isArray(body.detail)
            ? body.detail.map((d: { msg: string }) => d.msg.replace(/^Value error, /, '')).join('; ')
            : body.detail;
        throw new Error(detail || res.statusText);
    }
    return res.json();
}

export default function AlertsManager() {
    const globalTicker = useStore((s) => s.ticker);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [fired, setFired] = useState<Alert[]>([]);
    const [ticker, setTicker] = useState(globalTicker);
    const [conditionType, setConditionType] = useState('price_above');
    const [threshold, setThreshold] = useState('');
    const [permission, setPermission] = useState<NotificationPermission | 'unsupported'>(
        'Notification' in window ? Notification.permission : 'unsupported',
    );
    const [err, setErr] = useState('');

    const load = async () => {
        try {
            const [a, f] = await Promise.all([
                api<{ alerts: Alert[] }>('/api/alerts'),
                api<{ alerts: Alert[] }>('/api/alerts/triggered?limit=10'),
            ]);
            setAlerts(a.alerts);
            setFired(f.alerts);
            setErr('');
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        }
    };

    useEffect(() => {
        load();
        window.addEventListener(ALERTS_CHANGED, load);
        return () => window.removeEventListener(ALERTS_CHANGED, load);
    }, []);

    const createAlert = async (e: React.FormEvent) => {
        e.preventDefault();
        const value = parseFloat(threshold);
        if (!ticker.trim() || !Number.isFinite(value) || value <= 0) {
            setErr('Enter a ticker and a positive threshold.');
            return;
        }
        try {
            await api('/api/alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker.trim().toUpperCase(), condition_type: conditionType, threshold: value, user_id: 1 }),
            });
            setThreshold('');
            load();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        }
    };

    const deactivate = async (id: number) => {
        try {
            await api(`/api/alerts/${id}/deactivate`, { method: 'POST' });
            load();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        }
    };

    const enableNotifications = async () => {
        if (!('Notification' in window)) return;
        setPermission(await Notification.requestPermission());
    };

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <div className="mb-1 flex flex-wrap items-center justify-between gap-3">
                    <h2 className="section-heading">Alerts</h2>
                    {permission === 'default' && (
                        <button className="btn-secondary" style={{ fontSize: 11 }} onClick={enableNotifications}>
                            Enable desktop notifications
                        </button>
                    )}
                    {permission === 'granted' && <span className="badge-success text-[10px]">Desktop notifications on</span>}
                    {permission === 'denied' && (
                        <span className="text-xs text-white/40">
                            Desktop notifications are blocked in this browser — alerts still show in-app.
                        </span>
                    )}
                </div>
                <p className="mb-4 text-xs text-white/40">
                    Checked every minute while the terminal is open. Each alert fires once, then moves to “Recently fired”.
                </p>
                <form className="grid grid-cols-1 gap-3 md:grid-cols-4" onSubmit={createAlert}>
                    <input
                        className="input-field"
                        placeholder="Ticker"
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    />
                    <select className="input-field" value={conditionType} onChange={(e) => setConditionType(e.target.value)}>
                        {Object.entries(CONDITION_LABELS).map(([k, v]) => (
                            <option key={k} value={k}>
                                {v}
                            </option>
                        ))}
                    </select>
                    <input
                        className="input-field"
                        type="number"
                        step="0.01"
                        min="0"
                        placeholder={conditionType.startsWith('pe') ? 'P/E, e.g. 25' : 'Price, e.g. 190'}
                        value={threshold}
                        onChange={(e) => setThreshold(e.target.value)}
                    />
                    <button className="btn-primary" type="submit">
                        Create alert
                    </button>
                </form>
                {err && <ErrorNote msg={err} />}
            </div>

            <div className="card">
                <div className="border-b border-white/[0.06] p-4">
                    <h3 className="font-semibold">Active ({alerts.length})</h3>
                </div>
                <div className="divide-y divide-white/[0.03]">
                    {alerts.length === 0 && <div className="p-4 text-center text-sm text-white/50">No active alerts</div>}
                    {alerts.map((a) => (
                        <div key={a.id} className="flex items-center justify-between p-4">
                            <div>
                                <div className="font-mono font-semibold text-gold">{a.ticker}</div>
                                <div className="text-sm text-white/60">
                                    {CONDITION_LABELS[a.condition_type] ?? a.condition_type} {a.threshold}
                                </div>
                            </div>
                            <button className="text-sm text-rose hover:text-rose/80" onClick={() => deactivate(a.id)}>
                                Remove
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {fired.length > 0 && (
                <div className="card">
                    <div className="border-b border-white/[0.06] p-4">
                        <h3 className="font-semibold">Recently fired</h3>
                    </div>
                    <div className="divide-y divide-white/[0.03]">
                        {fired.map((a) => (
                            <div key={a.id} className="flex items-center justify-between p-4 text-sm">
                                <span>
                                    <span className="font-mono font-semibold text-gold">{a.ticker}</span>{' '}
                                    <span className="text-white/60">
                                        {CONDITION_LABELS[a.condition_type] ?? a.condition_type} {a.threshold}
                                    </span>
                                </span>
                                <span className="text-white/50">
                                    hit {a.triggered_value} · {a.triggered_at ? new Date(`${a.triggered_at}Z`).toLocaleString() : ''}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
