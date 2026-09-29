/**
 * Buy the Rumor, Sell the News - Event Timing Matrix
 * Visualizes temporal distance to macro/earnings/geopolitical events.
 * Events come from the backend's market_events table; when that table has
 * nothing (or the service is unreachable) this falls back to a small set of
 * hardcoded sample events — both cases carry a `source` field, and demo/
 * sample events are visibly badged below so it's never ambiguous whether
 * you're looking at real (`manual`) or placeholder (`demo`) data.
 */
import { useState, useEffect } from 'react';
import { ErrorNote } from './Terminal';
import { SectionCard } from './report/shared';
import { ANALYTICS_URL } from '../config';

interface Event {
    id: number;
    title: string;
    category: 'macro' | 'earnings' | 'geopolitical' | 'general';
    event_date: string;
    affected_assets: string[];
    consensus?: string;
    user_intuition?: string;
    exit_day?: number;
    source?: string;
}

export default function RumorNewsTiming() {
    const [events, setEvents] = useState<Event[]>([]);
    const [showAddForm, setShowAddForm] = useState(false);
    const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
    const [filter, setFilter] = useState('');
    const [err, setErr] = useState('');

    // Form state
    const [newEvent, setNewEvent] = useState({
        title: '',
        category: 'macro' as Event['category'],
        event_date: '',
        affected_assets: '',
    });

    useEffect(() => {
        loadEvents();
        const interval = setInterval(loadEvents, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const loadEvents = async () => {
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/market-events`);
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            const data = await res.json();
            setEvents(data.events?.length ? data.events : getSampleEvents());
            setErr('');
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
            setEvents(getSampleEvents());
        }
    };

    const addEvent = async () => {
        const assets = newEvent.affected_assets.split(',').map(a => a.trim().toUpperCase());
        try {
            const res = await fetch(`${ANALYTICS_URL}/api/market-events`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...newEvent,
                    affected_assets: assets,
                }),
            });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
            setNewEvent({ title: '', category: 'macro', event_date: '', affected_assets: '' });
            setShowAddForm(false);
            setErr('');
            loadEvents();
        } catch (e) {
            setErr(String(e instanceof Error ? e.message : e));
        }
    };

    const getDaysRemaining = (dateStr: string): number => {
        const eventDate = new Date(dateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return Math.ceil((eventDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    };

    const getUrgencyColor = (days: number): string => {
        if (days <= 3) return '#ef4444'; // Red
        if (days <= 7) return '#f59e0b'; // Yellow
        if (days <= 20) return '#10b981'; // Green
        return '#3b82f6'; // Blue
    };

    const getPhaseInfo = (days: number) => {
        if (days > 20) return { phase: 'Quiet Accumulation', desc: 'Ideal time to look for the rumor', progress: ((days - 20) / 10) * 100 };
        if (days > 9) return { phase: 'Quiet Accumulation', desc: 'Early entry window', progress: ((20 - days) / 11) * 100 };
        if (days > 2) return { phase: 'Mass Euphoria', desc: 'Media coverage builds, retail enters late', progress: ((9 - days) / 7) * 100 };
        return { phase: 'Danger Window', desc: 'CRITICAL ZONE — sell the news', progress: ((3 - days) / 4) * 100 };
    };

    const filteredEvents = filter
        ? events.filter(e => e.affected_assets.some(a => a.toLowerCase().includes(filter.toLowerCase())))
        : events;

    const categoryIcons = { macro: '📊', earnings: '💼', geopolitical: '🌍', general: '📰' };

    return (
        <div className="animate-fade-in space-y-4" style={{ fontFamily: 'var(--sans)' }}>
            {/* Header */}
            <div className="card p-6" style={{ background: 'linear-gradient(135deg, rgba(184,134,11,0.1) 0%, rgba(0,0,0,0.3) 100%)' }}>
                <div className="flex items-center justify-between mb-2">
                    <h1 className="text-3xl font-bold" style={{ color: 'var(--gold)' }}>
                        ⚡ Buy the Rumor, Sell the News
                    </h1>
                    <button className="btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
                        + Add Event
                    </button>
                </div>
                <p className="text-sm" style={{ color: 'var(--ink2)' }}>
                    Temporal-anticipation matrix — train your intuition by visualizing the exact distance to key events
                </p>
            </div>

            {err && <ErrorNote msg={err} />}

            {/* Add Event Form */}
            {showAddForm && (
                <SectionCard title="New Event" icon="➕">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <input
                            className="input-field"
                            placeholder="Event title"
                            value={newEvent.title}
                            onChange={e => setNewEvent({ ...newEvent, title: e.target.value })}
                        />
                        <select className="input-field" value={newEvent.category} onChange={e => setNewEvent({ ...newEvent, category: e.target.value as any })}>
                            <option value="macro">Macro</option>
                            <option value="earnings">Earnings</option>
                            <option value="geopolitical">Geopolitical</option>
                            <option value="general">General</option>
                        </select>
                        <input
                            className="input-field"
                            type="date"
                            value={newEvent.event_date}
                            onChange={e => setNewEvent({ ...newEvent, event_date: e.target.value })}
                        />
                        <input
                            className="input-field"
                            placeholder="Affected assets (comma-separated)"
                            value={newEvent.affected_assets}
                            onChange={e => setNewEvent({ ...newEvent, affected_assets: e.target.value })}
                        />
                    </div>
                    <button className="btn-primary mt-3" onClick={addEvent}>Save Event</button>
                </SectionCard>
            )}

            {/* Filter */}
            <div className="card p-4">
                <input
                    className="input-field"
                    placeholder="Filter by asset (e.g. Oil, Nasdaq, BTC)"
                    value={filter}
                    onChange={e => setFilter(e.target.value)}
                />
            </div>

            {/* Events Matrix */}
            <div className="space-y-3">
                {filteredEvents.map(event => {
                    const days = getDaysRemaining(event.event_date);
                    const phaseInfo = getPhaseInfo(days);
                    const urgencyColor = getUrgencyColor(days);

                    return (
                        <div
                            key={event.id}
                            className="card p-5 cursor-pointer hover:scale-[1.01] transition-transform"
                            onClick={() => setSelectedEvent(event)}
                            style={{ borderLeft: `4px solid ${urgencyColor}` }}
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="text-2xl">{categoryIcons[event.category]}</span>
                                        <div>
                                            <h3 className="font-bold text-lg" style={{ color: 'var(--gold)' }}>
                                                {event.title}
                                            </h3>
                                            <div className="flex gap-2 mt-1 items-center flex-wrap">
                                                {event.affected_assets.map(asset => (
                                                    <span key={asset} className="badge-accent text-xs">{asset}</span>
                                                ))}
                                                <a
                                                    href={`http://localhost:5175/?ticker=${encodeURIComponent(event.affected_assets[0] || '')}`}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={e => e.stopPropagation()}
                                                    className="text-xs"
                                                    style={{ color: 'var(--gold)', opacity: 0.75 }}
                                                    title="Opens Aeon Intelligence's own event view for this ticker — separate demo data, not shared with this app"
                                                >
                                                    View in Aeon Intelligence ↗
                                                </a>
                                                <a
                                                    href="http://localhost:5174"
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={e => e.stopPropagation()}
                                                    className="text-xs"
                                                    style={{ color: 'var(--gold)', opacity: 0.75 }}
                                                    title="Opens Aeon Platform's Data Studio — a separate app, not ticker-linked (it lives outside this codebase)"
                                                >
                                                    View in Aeon Platform ↗
                                                </a>
                                                {event.source === 'demo' && (
                                                    <span className="badge-gold text-xs" title="Placeholder sample event, not live market data">
                                                        DEMO DATA
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Days Countdown */}
                                <div className="text-center px-4 py-2 rounded-lg" style={{ background: `${urgencyColor}22`, border: `2px solid ${urgencyColor}` }}>
                                    <div className="text-3xl font-bold" style={{ color: urgencyColor }}>
                                        D-{days}
                                    </div>
                                    <div className="text-xs opacity-70">{new Date(event.event_date).toLocaleDateString()}</div>
                                </div>
                            </div>

                            {/* Phase Progress Bar */}
                            <div className="mt-4">
                                <div className="flex justify-between text-xs mb-1" style={{ color: 'var(--ink2)' }}>
                                    <span className="font-semibold">{phaseInfo.phase}</span>
                                    <span>{phaseInfo.desc}</span>
                                </div>
                                <div className="h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                                    <div
                                        className="h-full rounded-full transition-all duration-300"
                                        style={{ width: `${Math.min(100, Math.max(0, phaseInfo.progress))}%`, background: urgencyColor }}
                                    />
                                </div>
                            </div>

                            {/* Phase Stages */}
                            <div className="grid grid-cols-3 gap-2 mt-3 text-xs">
                                <div className="p-2 rounded text-center" style={{ background: days > 9 ? 'rgba(59,130,246,0.2)' : 'rgba(255,255,255,0.05)' }}>
                                    <div className="font-semibold">Accumulation</div>
                                    <div className="opacity-60">D-20 to D-10</div>
                                </div>
                                <div className="p-2 rounded text-center" style={{ background: days > 2 && days <= 9 ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.05)' }}>
                                    <div className="font-semibold">Euphoria</div>
                                    <div className="opacity-60">D-9 to D-2</div>
                                </div>
                                <div className="p-2 rounded text-center" style={{ background: days <= 2 ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.05)' }}>
                                    <div className="font-semibold">Danger</div>
                                    <div className="opacity-60">D-1 to D-0</div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Scenario Simulator Modal */}
            {selectedEvent && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.85)' }} onClick={() => setSelectedEvent(null)}>
                    <div className="card p-6 max-w-2xl w-full" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-start mb-4">
                            <h2 className="text-2xl font-bold" style={{ color: 'var(--gold)' }}>
                                Scenario Simulator
                            </h2>
                            <button onClick={() => setSelectedEvent(null)} className="text-2xl">✕</button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold mb-2">Consensus expectation</label>
                                <textarea className="input-field" rows={2} placeholder="What is the market expecting?" />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold mb-2">Your intuition</label>
                                <textarea className="input-field" rows={2} placeholder="What do you think will actually happen?" />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold mb-2">What is the price discounting today?</label>
                                    <input className="input-field" placeholder="Current-price analysis" />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold mb-2">Exact position-exit day</label>
                                    <input className="input-field" type="number" placeholder="D-X" />
                                </div>
                            </div>

                            <div className="p-4 rounded-lg" style={{ background: 'rgba(184,134,11,0.1)', border: '1px solid rgba(184,134,11,0.3)' }}>
                                <div className="font-semibold mb-2" style={{ color: 'var(--gold)' }}>Decision matrix</div>
                                <div className="text-sm space-y-1" style={{ color: 'var(--ink2)' }}>
                                    <div>✓ Enter during the accumulation phase (D-20 to D-10)</div>
                                    <div>✓ Monitor institutional flow</div>
                                    <div>✓ Exit before D-2 (danger window)</div>
                                    <div>⚠️ Never buy on D-1 or D-0</div>
                                </div>
                            </div>

                            <button className="btn-primary w-full">Save Analysis</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Placeholder sample events — used only when the backend has no events yet
// or is unreachable. Always carries source: 'demo' so the UI can badge it.
function getSampleEvents(): Event[] {
    const today = new Date();
    return [
        {
            id: 1,
            title: 'Upcoming US CPI Print',
            category: 'macro',
            event_date: new Date(today.getTime() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            affected_assets: ['SPY', 'NASDAQ', 'BONDS'],
            source: 'demo',
        },
        {
            id: 2,
            title: 'Nvidia Q4 Earnings',
            category: 'earnings',
            event_date: new Date(today.getTime() + 12 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            affected_assets: ['NVDA', 'SEMICONDUCTOR'],
            source: 'demo',
        },
        {
            id: 3,
            title: 'OPEC+ Summit — Production Decision',
            category: 'geopolitical',
            event_date: new Date(today.getTime() + 18 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            affected_assets: ['OIL', 'ENERGY'],
            source: 'demo',
        },
        {
            id: 4,
            title: 'Fed Meeting (FOMC)',
            category: 'macro',
            event_date: new Date(today.getTime() + 25 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            affected_assets: ['SPY', 'BONDS', 'GOLD'],
            source: 'demo',
        },
    ];
}
