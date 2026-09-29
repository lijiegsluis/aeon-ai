/**
 * Alerts & Notifications system
 * Monitor prices and metrics with desktop notifications
 */
import { useState, useEffect } from 'react';
import { ErrorNote } from './Terminal';
import { ANALYTICS_URL } from '../config';

interface Alert {
    id: number;
    ticker: string;
    condition_type: string;
    threshold: number;
    is_active: number;
    created_at: string;
}

export default function AlertsManager() {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [ticker, setTicker] = useState('');
    const [conditionType, setConditionType] = useState('price_above');
    const [threshold, setThreshold] = useState('');
    const [notificationsEnabled, setNotificationsEnabled] = useState(false);
    const [err, setErr] = useState('');

    useEffect(() => {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then((perm) => {
                setNotificationsEnabled(perm === 'granted');
            });
        } else {
            setNotificationsEnabled(Notification.permission === 'granted');
        }

        loadAlerts();
        const interval = setInterval(checkAlerts, 60000); // Check every minute
        return () => clearInterval(interval);
    }, []);

    const loadAlerts = async () => {
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/alerts`);
            const data = await res.json();
            setAlerts(data.alerts);
            setErr('');
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
        }
    };

    const createAlert = async () => {
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/alerts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: ticker.toUpperCase(),
                    condition_type: conditionType,
                    threshold: parseFloat(threshold),
                    user_id: 1, // TODO: actual user ID
                }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            setTicker('');
            setThreshold('');
            setErr('');
            loadAlerts();
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
        }
    };

    const deactivateAlert = async (id: number) => {
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/alerts/${id}/deactivate`, { method: 'POST' });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            setErr('');
            loadAlerts();
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
        }
    };

    const checkAlerts = async () => {
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/alerts/check`, { method: 'POST' });
            const data = await res.json();

            if (data.triggered.length > 0 && notificationsEnabled) {
                data.triggered.forEach((alert: any) => {
                    new Notification(`Alert: ${alert.ticker}`, {
                        body: `${alert.condition_type.replace('_', ' ')} ${alert.threshold} (current: ${alert.current_value})`,
                        icon: '/favicon.svg',
                    });
                });
            }
        } catch (e) {
            // Background poll (every 60s) — don't surface transient failures as a page-level error.
        }
    };

    const conditionLabels: Record<string, string> = {
        price_above: 'Price Above',
        price_below: 'Price Below',
        pe_above: 'P/E Above',
        pe_below: 'P/E Below',
    };

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <h2 className="section-heading mb-4">Alerts & Notifications</h2>

                {!notificationsEnabled && (
                    <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded text-sm text-yellow-500">
                        Desktop notifications are disabled. Enable them to receive alerts.
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
                    <input className="input-field" placeholder="Ticker" value={ticker} onChange={(e) => setTicker(e.target.value)} />
                    <select className="input-field" value={conditionType} onChange={(e) => setConditionType(e.target.value)}>
                        <option value="price_above">Price Above</option>
                        <option value="price_below">Price Below</option>
                        <option value="pe_above">P/E Above</option>
                        <option value="pe_below">P/E Below</option>
                    </select>
                    <input
                        className="input-field"
                        type="number"
                        step="0.01"
                        placeholder="Threshold"
                        value={threshold}
                        onChange={(e) => setThreshold(e.target.value)}
                    />
                    <button className="btn-primary" onClick={createAlert}>
                        Create Alert
                    </button>
                </div>
                {err && <ErrorNote msg={err} />}
            </div>

            <div className="card">
                <div className="p-4 border-b border-white/[0.06]">
                    <h3 className="font-semibold">Active Alerts ({alerts.length})</h3>
                </div>
                <div className="divide-y divide-white/[0.03]">
                    {alerts.length === 0 && <div className="p-4 text-center text-white/50 text-sm">No active alerts</div>}
                    {alerts.map((alert) => (
                        <div key={alert.id} className="p-4 flex items-center justify-between">
                            <div>
                                <div className="font-mono font-semibold text-gold">{alert.ticker}</div>
                                <div className="text-sm text-white/60">
                                    {conditionLabels[alert.condition_type]} {alert.threshold}
                                </div>
                            </div>
                            <button className="text-sm text-rose hover:text-rose/80" onClick={() => deactivateAlert(alert.id)}>
                                Deactivate
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
