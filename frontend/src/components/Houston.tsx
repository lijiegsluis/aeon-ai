/**
 * Houston — Research-ops tab for Aeon Nimbus Analysis.
 * Three panels: Brief (morning synthesis), Gates (thesis gates), Notes (KB).
 * All data lives in ~/AeonNimbus/.
 */
import { useEffect, useState } from 'react';
import { jget, jpost } from '../utils/api';
import { ErrorNote } from './Terminal';
import { SectionCard } from './report/shared';
import { ANALYTICS_URL } from '../config';

const AN = ANALYTICS_URL;

// ── Brief panel ───────────────────────────────────────────────────────────────

function BriefPanel() {
    const [brief, setBrief] = useState<string | null>(null);
    const [day, setDay] = useState('');
    const [running, setRunning] = useState(false);
    const [err, setErr] = useState('');

    useEffect(() => {
        load();
    }, []);

    async function load() {
        try {
            const d = await jget<{ ok: boolean; brief: string | null; day: string }>(`${AN}/houston/brief`);
            setDay(d.day);
            setBrief(d.brief);
        } catch (e: any) {
            setErr(e.message);
        }
    }

    async function run() {
        setRunning(true);
        setErr('');
        try {
            const d = await jpost<{ ok: boolean; brief: string; day: string }>(`${AN}/houston/run`, {});
            setDay(d.day);
            setBrief(d.brief);
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setRunning(false);
        }
    }

    return (
        <SectionCard title="Morning Brief" icon="🌅">
            <div className="flex items-center gap-3 mb-3">
                <span className="text-xs text-ink2">{day ? `${day}` : 'No brief yet today'}</span>
                <button onClick={run} disabled={running} className="btn-primary ml-auto" style={{ opacity: running ? 0.5 : 1 }}>
                    {running ? 'Running…' : '▶ Run Houston'}
                </button>
            </div>
            {err && (
                <div className="mb-3">
                    <ErrorNote msg={err} />
                </div>
            )}
            {brief ? (
                <pre className="text-sm leading-relaxed whitespace-pre-wrap" style={{ fontFamily: 'inherit' }}>
                    {brief}
                </pre>
            ) : (
                !err && (
                    <div className="text-ink2 text-sm text-center py-6">
                        No brief for today. Click <b>Run Houston</b> to generate one.
                    </div>
                )
            )}
        </SectionCard>
    );
}

// ── Gates panel ───────────────────────────────────────────────────────────────

type Gate = { ticker: string; file: string; entry?: string; target?: string; stop?: string; size?: string; kill?: string };

const blank = { ticker: '', edge: '', catalyst: '', entry: '', target: '', stop: '', size: '4%', kill: '' };

function GatesPanel() {
    const [gates, setGates] = useState<Gate[]>([]);
    const [form, setForm] = useState(blank);
    const [saving, setSaving] = useState(false);
    const [err, setErr] = useState('');
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        load();
    }, []);
    async function load() {
        try {
            const d = await jget<{ gates: Gate[] }>(`${AN}/houston/gates`);
            setGates(d.gates);
        } catch (e: any) {
            setErr(e.message);
        }
    }
    async function save() {
        if (!form.ticker || !form.edge || !form.kill || !form.entry) {
            setErr('Fill ticker, edge, entry, and kill condition.');
            return;
        }
        setSaving(true);
        setErr('');
        try {
            await jpost(`${AN}/houston/gates`, form);
            setForm(blank);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
            load();
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setSaving(false);
        }
    }
    const inp = (k: keyof typeof blank, ph: string) => (
        <input
            value={form[k]}
            onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.value }))}
            placeholder={ph}
            className="input-field flex-1"
        />
    );

    return (
        <div className="flex flex-col gap-4">
            {/* Add gate form */}
            <SectionCard title="New Thesis Gate" icon="🛡">
                <div className="flex gap-2 mb-2">
                    {inp('ticker', 'Ticker')} {inp('entry', 'Entry')} {inp('target', 'Target')}
                    {inp('stop', 'Stop')} {inp('size', 'Size')}
                </div>
                <textarea
                    value={form.edge}
                    onChange={(e) => setForm((f) => ({ ...f, edge: e.target.value }))}
                    placeholder="LINE 1 — EDGE: What the company does that competitors cannot replicate, and why the market doesn't price it."
                    rows={2}
                    className="input-field mb-2"
                    style={{ resize: 'vertical' }}
                />
                <textarea
                    value={form.catalyst}
                    onChange={(e) => setForm((f) => ({ ...f, catalyst: e.target.value }))}
                    placeholder="LINE 2 — CATALYST: Specific event with a named date range that will reprice this."
                    rows={2}
                    className="input-field mb-2"
                    style={{ resize: 'vertical' }}
                />
                <textarea
                    value={form.kill}
                    onChange={(e) => setForm((f) => ({ ...f, kill: e.target.value }))}
                    placeholder="LINE 4 — KILL CONDITION: Single observable fact that invalidates the thesis and requires immediate exit."
                    rows={2}
                    className="input-field"
                    style={{ resize: 'vertical' }}
                />
                {err && (
                    <div className="mt-2">
                        <ErrorNote msg={err} />
                    </div>
                )}
                <div className="flex justify-end items-center mt-2.5 gap-2">
                    {saved && <span className="text-xs text-emerald">Saved.</span>}
                    <button onClick={save} disabled={saving} className="btn-primary" style={{ opacity: saving ? 0.5 : 1 }}>
                        {saving ? 'Saving…' : 'Save Gate'}
                    </button>
                </div>
            </SectionCard>
            {/* Existing gates */}
            {gates.map((g) => (
                <div key={g.file} className="card p-3.5">
                    <div className="flex gap-2.5 items-center mb-1.5 flex-wrap">
                        <span className="font-bold text-sm">{g.ticker}</span>
                        {g.entry && <span className="text-xs text-ink2">Entry {g.entry}</span>}
                        {g.target && <span className="text-xs text-emerald">→ {g.target}</span>}
                        {g.stop && <span className="text-xs text-rose">Stop {g.stop}</span>}
                        {g.size && <span className="text-xs text-ink2">| {g.size}</span>}
                        <a
                            href={`http://localhost:5175/?ticker=${encodeURIComponent(g.ticker)}`}
                            target="_blank"
                            rel="noopener noreferrer"
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
                            className="text-xs"
                            style={{ color: 'var(--gold)', opacity: 0.75 }}
                            title="Opens Aeon Platform's Data Studio — a separate app, not ticker-linked (it lives outside this codebase)"
                        >
                            View in Aeon Platform ↗
                        </a>
                        <span className="text-[11px] text-ink3 ml-auto">{g.file}</span>
                    </div>
                    {g.kill && (
                        <div className="text-xs leading-relaxed" style={{ color: 'var(--gold2)' }}>
                            <b>Kill: </b>
                            {g.kill}
                        </div>
                    )}
                </div>
            ))}
            {!gates.length && (
                <div className="text-ink2 text-sm text-center py-6">No gates on file. Write a gate before sizing any position.</div>
            )}
        </div>
    );
}

// ── Notes panel ───────────────────────────────────────────────────────────────

type Note = { id: number; date: string; task: string; tickers: string; finding: string; created_at: string };

function NotesPanel() {
    const [notes, setNotes] = useState<Note[]>([]);
    const [filter, setFilter] = useState('');
    const [form, setForm] = useState({ date: '', task: '', tickers: '', finding: '' });
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [err, setErr] = useState('');

    useEffect(() => {
        load();
    }, [filter]);
    async function load() {
        try {
            const url = `${AN}/houston/notes` + (filter ? `?ticker=${encodeURIComponent(filter)}` : '');
            const d = await jget<{ notes: Note[] }>(url);
            setNotes(d.notes);
        } catch (e: any) {
            setErr(e.message);
        }
    }
    async function save() {
        if (!form.finding.trim()) {
            setErr('Finding cannot be empty.');
            return;
        }
        setSaving(true);
        setErr('');
        try {
            await jpost(`${AN}/houston/notes`, form);
            setForm({ date: '', task: '', tickers: '', finding: '' });
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
            load();
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="flex flex-col gap-3.5">
            {/* Add note */}
            <SectionCard title="Add Research Finding" icon="📚">
                <div className="flex gap-2 mb-2">
                    <input
                        value={form.date}
                        onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
                        type="date"
                        className="input-field"
                        style={{ width: 'auto' }}
                    />
                    <input
                        value={form.task}
                        onChange={(e) => setForm((f) => ({ ...f, task: e.target.value }))}
                        placeholder="Task (task5, doocey, manual)"
                        className="input-field flex-1"
                    />
                    <input
                        value={form.tickers}
                        onChange={(e) => setForm((f) => ({ ...f, tickers: e.target.value }))}
                        placeholder="Tickers (ORCL, MELI)"
                        className="input-field flex-1"
                    />
                </div>
                <textarea
                    value={form.finding}
                    onChange={(e) => setForm((f) => ({ ...f, finding: e.target.value }))}
                    placeholder="Finding — the insight, risk, or data point worth remembering…"
                    rows={3}
                    className="input-field"
                    style={{ resize: 'vertical' }}
                />
                {err && (
                    <div className="mt-2">
                        <ErrorNote msg={err} />
                    </div>
                )}
                <div className="flex justify-end items-center gap-2 mt-2">
                    {saved && <span className="text-xs text-emerald">Saved.</span>}
                    <button onClick={save} disabled={saving} className="btn-primary" style={{ opacity: saving ? 0.5 : 1 }}>
                        {saving ? 'Saving…' : 'Save Finding'}
                    </button>
                </div>
            </SectionCard>
            {/* Filter + list */}
            <div className="flex gap-2">
                <input
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    placeholder="Filter by ticker…"
                    className="input-field"
                    style={{ maxWidth: 200 }}
                />
                <button onClick={load} className="btn-secondary">
                    ↻
                </button>
            </div>
            {notes.map((n) => (
                <div key={n.id} className="card p-3.5">
                    <div className="flex gap-2 items-center mb-1.5 flex-wrap">
                        {n.tickers && <span className="font-bold text-[13px]">{n.tickers}</span>}
                        {n.task && <span className="badge-nebula">{n.task}</span>}
                        <span className="text-[11px] text-ink3 ml-auto">{n.date || n.created_at?.slice(0, 10)}</span>
                    </div>
                    <div className="text-sm leading-relaxed">{n.finding}</div>
                </div>
            ))}
            {!notes.length && <div className="text-ink2 text-sm text-center py-6">No notes yet. Add a finding above.</div>}
        </div>
    );
}

// ── Main tab ──────────────────────────────────────────────────────────────────

type Panel = 'brief' | 'gates' | 'notes';

export default function HoustonTab() {
    const [panel, setPanel] = useState<Panel>('brief');
    const tabs: { id: Panel; label: string }[] = [
        { id: 'brief', label: '🌅 Morning Brief' },
        { id: 'gates', label: '🛡 Thesis Gates' },
        { id: 'notes', label: '📚 Knowledge Base' },
    ];

    return (
        <div className="animate-fade-in" style={{ maxWidth: 860, margin: '0 auto', padding: '24px 16px 60px' }}>
            <div className="mb-5">
                <h2 className="text-xl font-bold mb-1">Houston</h2>
                <p className="text-sm text-ink2">
                    Research-ops layer — morning brief, thesis gates, knowledge base. Every figure sourced. Every position gated before
                    sizing.
                </p>
            </div>
            {/* Sub-nav */}
            <div className="flex gap-0.5 mb-5" style={{ borderBottom: '1px solid var(--rule2)' }}>
                {tabs.map((t) => (
                    <button
                        key={t.id}
                        onClick={() => setPanel(t.id)}
                        className="text-sm px-4 py-2"
                        style={{
                            background: 'transparent',
                            border: 'none',
                            borderBottom: panel === t.id ? '2px solid var(--gold)' : '2px solid transparent',
                            color: panel === t.id ? 'var(--gold)' : 'var(--ink2)',
                            cursor: 'pointer',
                            fontWeight: panel === t.id ? 600 : 400,
                        }}
                    >
                        {t.label}
                    </button>
                ))}
            </div>
            {panel === 'brief' && <BriefPanel />}
            {panel === 'gates' && <GatesPanel />}
            {panel === 'notes' && <NotesPanel />}
        </div>
    );
}
