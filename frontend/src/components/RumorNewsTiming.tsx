/**
 * Buy the Rumor, Sell the News — event timing matrix.
 * Upcoming events from the backend's market_events table, each with its D-X
 * countdown, phase, the rule engine's read, and your own saved plan (consensus,
 * intuition, exit day). When the backend is unreachable a few sample events are
 * shown instead, always badged DEMO DATA.
 */
import { useEffect, useState } from 'react';
import { ErrorNote } from './Terminal';
import { SectionCard } from './report/shared';
import { ANALYTICS_URL, PLATFORM_APP_URL, intelligenceTickerUrl } from '../config';
import { jdelete, jget, jpost } from '../utils/api';
import { useStore } from '../store';

interface Analysis {
    sentiment_score?: number;
    sentiment_label?: string;
    reasoning?: string;
    recommended_action?: string;
    affected_assets?: { ticker: string; match_type: string }[];
}

interface Event {
    id: number;
    title: string;
    category: 'macro' | 'earnings' | 'geopolitical' | 'general';
    event_date: string;
    affected_assets: string[];
    raw_text?: string;
    source?: string;
    analysis?: Analysis;
}

type Plan = { consensus: string; intuition: string; discounting: string; exitDay: string; savedAt?: string };
const PLAN_KEY = 'aeonnimbus_event_plans';
const emptyPlan: Plan = { consensus: '', intuition: '', discounting: '', exitDay: '' };

function loadPlans(): Record<string, Plan> {
    try {
        return JSON.parse(localStorage.getItem(PLAN_KEY) || '{}');
    } catch {
        return {};
    }
}

/** "2026-10-14" is a calendar date, not a UTC instant — parse it as local midnight
 * so the countdown doesn't slip a day west of Greenwich. */
function parseLocalDate(s: string): Date {
    const [y, m, d] = s.slice(0, 10).split('-').map(Number);
    return new Date(y, (m || 1) - 1, d || 1);
}

function daysUntil(s: string): number {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.round((parseLocalDate(s).getTime() - today.getTime()) / 86400000);
}

const urgencyColor = (days: number) => (days <= 2 ? '#ef4444' : days <= 9 ? '#f59e0b' : days <= 20 ? '#10b981' : '#3b82f6');

function phaseInfo(days: number) {
    if (days > 20) return { phase: 'Pre-rumor', desc: 'Too early — the market is not pricing it yet', progress: 0 };
    if (days > 9) return { phase: 'Accumulation', desc: 'Early entry window', progress: ((20 - days) / 20) * 100 };
    if (days > 2) return { phase: 'Euphoria', desc: 'Coverage builds, retail arrives late', progress: ((20 - days) / 20) * 100 };
    return { phase: 'Danger window', desc: 'Sell-the-news zone', progress: 100 };
}

const categoryIcons = { macro: '📊', earnings: '💼', geopolitical: '🌍', general: '📰' };

export default function RumorNewsTiming() {
    const [events, setEvents] = useState<Event[]>([]);
    const [pastEvents, setPastEvents] = useState<Event[]>([]);
    const [isDemo, setIsDemo] = useState(false);
    const [showAddForm, setShowAddForm] = useState(false);
    const [selected, setSelected] = useState<Event | null>(null);
    const [plans, setPlans] = useState<Record<string, Plan>>(loadPlans);
    const [draft, setDraft] = useState<Plan>(emptyPlan);
    const [filter, setFilter] = useState('');
    const [showPast, setShowPast] = useState(false);
    const [err, setErr] = useState('');
    const setTicker = useStore((s) => s.setTicker);
    const [newEvent, setNewEvent] = useState({ title: '', category: 'macro' as Event['category'], event_date: '', affected_assets: '' });

    const load = async () => {
        try {
            const data = await jget<{ events: Event[] }>(`${ANALYTICS_URL}/api/market-events?include_past=true&limit=300`);
            const all = data.events ?? [];
            setEvents(all.filter((e) => daysUntil(e.event_date) >= 0));
            setPastEvents(all.filter((e) => daysUntil(e.event_date) < 0).reverse());
            setIsDemo(false);
            setErr('');
        } catch (e) {
            setErr(String(e));
            setEvents(sampleEvents());
            setPastEvents([]);
            setIsDemo(true);
        }
    };

    useEffect(() => {
        load();
        const id = setInterval(load, 60000);
        return () => clearInterval(id);
    }, []);

    const addEvent = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newEvent.title.trim() || !newEvent.event_date) {
            setErr('An event needs a title and a date.');
            return;
        }
        const assets = newEvent.affected_assets
            .split(/[\s,]+/)
            .map((a) => a.trim().toUpperCase())
            .filter(Boolean);
        try {
            await jpost(`${ANALYTICS_URL}/api/market-events`, { ...newEvent, source: 'manual', affected_assets: assets });
            setNewEvent({ title: '', category: 'macro', event_date: '', affected_assets: '' });
            setShowAddForm(false);
            load();
        } catch (e) {
            setErr(String(e));
        }
    };

    const removeEvent = async (id: number) => {
        try {
            await jdelete(`${ANALYTICS_URL}/api/market-events/${id}`);
            setSelected(null);
            load();
        } catch (e) {
            setErr(String(e));
        }
    };

    const openEvent = (ev: Event) => {
        setSelected(ev);
        setDraft(plans[String(ev.id)] ?? emptyPlan);
    };

    const savePlan = () => {
        if (!selected) return;
        const next = { ...plans, [String(selected.id)]: { ...draft, savedAt: new Date().toISOString() } };
        setPlans(next);
        localStorage.setItem(PLAN_KEY, JSON.stringify(next));
        setSelected(null);
    };

    const q = filter.trim().toLowerCase();
    const matches = (e: Event) => !q || e.title.toLowerCase().includes(q) || e.affected_assets.some((a) => a.toLowerCase().includes(q));
    const shown = events.filter(matches);
    const shownPast = pastEvents.filter(matches);

    return (
        <div className="animate-fade-in space-y-4" style={{ fontFamily: 'var(--sans)' }}>
            <div className="card p-6" style={{ background: 'linear-gradient(135deg, rgba(184,134,11,0.1) 0%, rgba(0,0,0,0.3) 100%)' }}>
                <div className="mb-2 flex items-center justify-between gap-3">
                    <h1 className="text-3xl font-bold" style={{ color: 'var(--gold)' }}>
                        ⚡ Buy the Rumor, Sell the News
                    </h1>
                    <button className="btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
                        + Add event
                    </button>
                </div>
                <p className="text-sm" style={{ color: 'var(--ink2)' }}>
                    Every upcoming catalyst with its exact distance, its phase, and your plan for it. Click an event to write the plan.
                </p>
            </div>

            {err && <ErrorNote msg={err} />}
            {isDemo && <p className="text-xs text-gold-light">Showing sample events while the analytics service is unreachable.</p>}

            {showAddForm && (
                <SectionCard title="New event" icon="➕">
                    <form onSubmit={addEvent}>
                        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                            <input
                                className="input-field"
                                placeholder="Event title, e.g. NVDA Q3 earnings"
                                value={newEvent.title}
                                onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                            />
                            <select
                                className="input-field"
                                value={newEvent.category}
                                onChange={(e) => setNewEvent({ ...newEvent, category: e.target.value as Event['category'] })}
                            >
                                <option value="macro">Macro</option>
                                <option value="earnings">Earnings</option>
                                <option value="geopolitical">Geopolitical</option>
                                <option value="general">General</option>
                            </select>
                            <input
                                className="input-field"
                                type="date"
                                value={newEvent.event_date}
                                onChange={(e) => setNewEvent({ ...newEvent, event_date: e.target.value })}
                            />
                            <input
                                className="input-field"
                                placeholder="Affected tickers, e.g. NVDA AMD SMH"
                                value={newEvent.affected_assets}
                                onChange={(e) => setNewEvent({ ...newEvent, affected_assets: e.target.value })}
                            />
                        </div>
                        <button className="btn-primary mt-3" type="submit">
                            Save event
                        </button>
                    </form>
                </SectionCard>
            )}

            <div className="card p-4">
                <input
                    className="input-field"
                    placeholder="Filter by ticker or title (e.g. NVDA, CPI, oil)"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                />
            </div>

            <div className="space-y-3">
                {shown.length === 0 && (
                    <div className="card p-8 text-center text-white/50">No upcoming events{q ? ' match that filter' : ''}.</div>
                )}
                {shown.map((event) => {
                    const days = daysUntil(event.event_date);
                    const phase = phaseInfo(days);
                    const color = urgencyColor(days);
                    const plan = plans[String(event.id)];
                    const exitDay = plan?.exitDay ? Number(plan.exitDay) : null;
                    return (
                        <div
                            key={event.id}
                            className="card cursor-pointer p-5 transition-transform hover:scale-[1.01]"
                            onClick={() => openEvent(event)}
                            style={{ borderLeft: `4px solid ${color}` }}
                        >
                            <div className="mb-3 flex items-start justify-between gap-4">
                                <div className="flex flex-1 items-center gap-3">
                                    <span className="text-2xl">{categoryIcons[event.category] ?? '📰'}</span>
                                    <div>
                                        <h3 className="text-lg font-bold" style={{ color: 'var(--gold)' }}>
                                            {event.title}
                                        </h3>
                                        <div className="mt-1 flex flex-wrap items-center gap-2">
                                            {event.affected_assets.map((asset) => (
                                                <button
                                                    key={asset}
                                                    className="badge-accent text-xs"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setTicker(asset);
                                                    }}
                                                    title={`Make ${asset} the terminal ticker`}
                                                >
                                                    {asset}
                                                </button>
                                            ))}
                                            {event.affected_assets[0] && (
                                                <a
                                                    href={intelligenceTickerUrl(event.affected_assets[0])}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="text-xs"
                                                    style={{ color: 'var(--gold)', opacity: 0.75 }}
                                                    title="Timing, news and insider activity for this ticker in Aeon Intelligence"
                                                >
                                                    {event.affected_assets[0]} in Intelligence ↗
                                                </a>
                                            )}
                                            <a
                                                href={PLATFORM_APP_URL}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                onClick={(e) => e.stopPropagation()}
                                                className="text-xs"
                                                style={{ color: 'var(--gold)', opacity: 0.75 }}
                                            >
                                                Aeon Platform ↗
                                            </a>
                                            {event.source === 'demo' && <span className="badge-gold text-xs">DEMO DATA</span>}
                                            {plan && (
                                                <span className="badge-success text-xs">
                                                    plan saved{exitDay != null ? ` · exit D-${exitDay}` : ''}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div
                                    className="rounded-lg px-4 py-2 text-center"
                                    style={{ background: `${color}22`, border: `2px solid ${color}` }}
                                >
                                    <div className="text-3xl font-bold" style={{ color }}>
                                        D-{days}
                                    </div>
                                    <div className="text-xs opacity-70">{parseLocalDate(event.event_date).toLocaleDateString()}</div>
                                </div>
                            </div>

                            <div className="mt-4">
                                <div className="mb-1 flex justify-between text-xs" style={{ color: 'var(--ink2)' }}>
                                    <span className="font-semibold">{phase.phase}</span>
                                    <span>
                                        {exitDay != null && days <= exitDay ? `⚠️ past your planned exit (D-${exitDay})` : phase.desc}
                                    </span>
                                </div>
                                <div className="h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}>
                                    <div
                                        className="h-full rounded-full"
                                        style={{ width: `${Math.min(100, Math.max(2, phase.progress))}%`, background: color }}
                                    />
                                </div>
                            </div>

                            <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                                {[
                                    ['Accumulation', 'D-20 to D-10', days > 9 && days <= 20, 'rgba(16,185,129,0.2)'],
                                    ['Euphoria', 'D-9 to D-3', days > 2 && days <= 9, 'rgba(245,158,11,0.2)'],
                                    ['Danger', 'D-2 to D-0', days <= 2, 'rgba(239,68,68,0.2)'],
                                ].map(([label, range, on, bg]) => (
                                    <div
                                        key={label as string}
                                        className="rounded p-2 text-center"
                                        style={{ background: on ? (bg as string) : 'rgba(255,255,255,0.05)' }}
                                    >
                                        <div className="font-semibold">{label as string}</div>
                                        <div className="opacity-60">{range as string}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>

            {pastEvents.length > 0 && (
                <div className="card p-4">
                    <button className="text-sm text-white/60 hover:text-white" onClick={() => setShowPast(!showPast)}>
                        {showPast ? '▾' : '▸'} Past events ({shownPast.length}) — review how your plans played out
                    </button>
                    {showPast && (
                        <div className="mt-3 divide-y divide-white/[0.04]">
                            {shownPast.map((e) => (
                                <div
                                    key={e.id}
                                    className="flex cursor-pointer items-center justify-between py-2 text-sm"
                                    onClick={() => openEvent(e)}
                                >
                                    <span>
                                        <span className="text-white/40">{parseLocalDate(e.event_date).toLocaleDateString()}</span> ·{' '}
                                        {e.title}
                                    </span>
                                    {plans[String(e.id)] && <span className="badge-success text-[10px]">plan</span>}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {selected && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center p-4"
                    style={{ background: 'rgba(0,0,0,0.85)' }}
                    onClick={() => setSelected(null)}
                >
                    <div className="card max-h-[90vh] w-full max-w-2xl overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
                        <div className="mb-4 flex items-start justify-between gap-4">
                            <div>
                                <p className="stat-label">Event plan · D-{daysUntil(selected.event_date)}</p>
                                <h2 className="text-2xl font-bold" style={{ color: 'var(--gold)' }}>
                                    {selected.title}
                                </h2>
                            </div>
                            <button onClick={() => setSelected(null)} className="text-2xl" aria-label="Close">
                                ✕
                            </button>
                        </div>

                        {selected.analysis?.reasoning && (
                            <div className="mb-4 rounded-lg p-3 text-sm" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                <div className="mb-1 flex items-center gap-2">
                                    <span className="stat-label">Rule engine read</span>
                                    {selected.analysis.sentiment_label && (
                                        <span className="badge text-[10px]">
                                            {selected.analysis.sentiment_label} ({selected.analysis.sentiment_score})
                                        </span>
                                    )}
                                    {selected.analysis.recommended_action && (
                                        <span className="text-xs">{selected.analysis.recommended_action}</span>
                                    )}
                                </div>
                                <p className="text-xs leading-relaxed text-white/60">
                                    {selected.analysis.reasoning.split(' | ').join(' · ')}
                                </p>
                                <p className="mt-1 text-[10px] text-white/30">
                                    Deterministic keyword and day-count rules — not a model forecast.
                                </p>
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label className="mb-2 block text-sm font-semibold">Consensus expectation</label>
                                <textarea
                                    className="input-field"
                                    rows={2}
                                    placeholder="What is the market expecting?"
                                    value={draft.consensus}
                                    onChange={(e) => setDraft({ ...draft, consensus: e.target.value })}
                                />
                            </div>
                            <div>
                                <label className="mb-2 block text-sm font-semibold">Your intuition</label>
                                <textarea
                                    className="input-field"
                                    rows={2}
                                    placeholder="What do you think will actually happen?"
                                    value={draft.intuition}
                                    onChange={(e) => setDraft({ ...draft, intuition: e.target.value })}
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="mb-2 block text-sm font-semibold">What is the price discounting today?</label>
                                    <input
                                        className="input-field"
                                        placeholder="e.g. a 5% beat is priced in"
                                        value={draft.discounting}
                                        onChange={(e) => setDraft({ ...draft, discounting: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="mb-2 block text-sm font-semibold">Planned exit (days before)</label>
                                    <input
                                        className="input-field"
                                        type="number"
                                        min={0}
                                        max={60}
                                        placeholder="e.g. 3 for D-3"
                                        value={draft.exitDay}
                                        onChange={(e) => setDraft({ ...draft, exitDay: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div
                                className="rounded-lg p-4"
                                style={{ background: 'rgba(184,134,11,0.1)', border: '1px solid rgba(184,134,11,0.3)' }}
                            >
                                <div className="mb-2 font-semibold" style={{ color: 'var(--gold)' }}>
                                    Decision checklist
                                </div>
                                <div className="space-y-1 text-sm" style={{ color: 'var(--ink2)' }}>
                                    <div>✓ Enter during accumulation (D-20 to D-10)</div>
                                    <div>✓ Write the exit day down before entering</div>
                                    <div>✓ Be out before the danger window (D-2)</div>
                                    <div>⚠️ Never initiate on D-1 or D-0</div>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <button className="btn-primary flex-1" onClick={savePlan}>
                                    Save plan
                                </button>
                                {!isDemo && (
                                    <button className="btn-secondary" onClick={() => removeEvent(selected.id)}>
                                        Delete event
                                    </button>
                                )}
                            </div>
                            <p className="text-[10px] text-white/30">Plans are stored in this browser only.</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Placeholder events shown only when the analytics service is unreachable — always badged DEMO DATA.
function sampleEvents(): Event[] {
    const inDays = (n: number) => {
        const d = new Date();
        d.setDate(d.getDate() + n);
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    };
    return [
        {
            id: -1,
            title: 'US CPI print (sample)',
            category: 'macro',
            event_date: inDays(5),
            affected_assets: ['SPY', 'TLT'],
            source: 'demo',
        },
        {
            id: -2,
            title: 'NVIDIA earnings (sample)',
            category: 'earnings',
            event_date: inDays(12),
            affected_assets: ['NVDA', 'SMH'],
            source: 'demo',
        },
        {
            id: -3,
            title: 'FOMC decision (sample)',
            category: 'macro',
            event_date: inDays(25),
            affected_assets: ['SPY', 'GLD'],
            source: 'demo',
        },
    ];
}
