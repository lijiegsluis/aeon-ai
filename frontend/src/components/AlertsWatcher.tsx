/**
 * Background alert checker — mounted once for the whole app, renders nothing but
 * toasts. Every minute it asks the backend to evaluate active alerts; each alert
 * fires once (the backend switches it off), shows an in-app toast, and — if the
 * user has allowed it — a desktop notification.
 */
import { useEffect, useState } from 'react';
import { ANALYTICS_URL } from '../config';
import { useStore } from '../store';

type Fired = { id: number; ticker: string; condition_type: string; threshold: number; current_value: number };

export const CONDITION_LABELS: Record<string, string> = {
    price_above: 'Price above',
    price_below: 'Price below',
    pe_above: 'P/E above',
    pe_below: 'P/E below',
};

export const ALERTS_CHANGED = 'aeon:alerts-changed';

export default function AlertsWatcher() {
    const [toasts, setToasts] = useState<Fired[]>([]);
    const setTicker = useStore((s) => s.setTicker);

    useEffect(() => {
        const check = async () => {
            if (document.visibilityState !== 'visible' && !('Notification' in window && Notification.permission === 'granted')) return;
            try {
                const res = await fetch(`${ANALYTICS_URL}/api/alerts/check`, { method: 'POST' });
                if (!res.ok) return;
                const data: { triggered: Fired[] } = await res.json();
                if (!data.triggered?.length) return;
                setToasts((t) => [...t, ...data.triggered].slice(-4));
                window.dispatchEvent(new Event(ALERTS_CHANGED));
                // Read the permission now, not at mount — the user may have granted it since.
                if ('Notification' in window && Notification.permission === 'granted') {
                    data.triggered.forEach((a) => {
                        new Notification(`Aeon alert · ${a.ticker}`, {
                            body: `${CONDITION_LABELS[a.condition_type] ?? a.condition_type} ${a.threshold} — now ${a.current_value}`,
                            icon: '/favicon.svg',
                            tag: `aeon-alert-${a.id}`,
                        });
                    });
                }
            } catch {
                /* backend offline — try again next minute */
            }
        };
        check();
        const id = setInterval(check, 60000);
        return () => clearInterval(id);
    }, []);

    if (!toasts.length) return null;
    return (
        <div style={{ position: 'fixed', right: 20, bottom: 20, zIndex: 100, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {toasts.map((a) => (
                <div key={a.id} className="card-premium animate-fade-in" style={{ padding: '12px 14px', minWidth: 260 }} role="status">
                    <div className="flex items-center justify-between gap-3">
                        <button
                            className="font-mono font-bold text-gold"
                            style={{ background: 'none', border: 0, cursor: 'pointer', padding: 0 }}
                            onClick={() => setTicker(a.ticker)}
                            title={`Make ${a.ticker} the terminal ticker`}
                        >
                            🔔 {a.ticker}
                        </button>
                        <button
                            aria-label="Dismiss"
                            className="text-white/40 hover:text-white"
                            style={{ background: 'none', border: 0, cursor: 'pointer' }}
                            onClick={() => setToasts((t) => t.filter((x) => x.id !== a.id))}
                        >
                            ✕
                        </button>
                    </div>
                    <p className="mt-1 text-sm text-white/75">
                        {CONDITION_LABELS[a.condition_type] ?? a.condition_type} {a.threshold} — now{' '}
                        <span className="font-mono">{a.current_value}</span>
                    </p>
                </div>
            ))}
        </div>
    );
}
