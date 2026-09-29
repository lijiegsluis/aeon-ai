/**
 * Deep Reports — native Aeon rebuild of the equity-research report engine.
 * Drives its REST API (:8002) directly: submit a job, stream the pipeline
 * log in the terminal's own style, then present the finished report
 * document. No embedded app chrome — one room in the product.
 */
import { useEffect, useRef, useState } from 'react';
import { ErrorNote, ProgressBar, useVaultKey, VaultKeyStatus } from './Terminal';
import { useStore } from '../store';
import { ANALYTICS_URL, FINROBOT_URL } from '../config';
import { jget } from '../utils/api';

const FINROBOT = FINROBOT_URL;

type TaskResult = { ticker: string; html: string[]; pdf: string[] };
type TaskState = { status: string; logs: string[]; result: TaskResult | null };

/** Estimate progress + a human phase label from the pipeline's log stream. */
function phaseFromLogs(logs: string[]): { pct: number; label: string } {
    const text = logs.join('\n').toLowerCase();
    if (text.includes('pipeline completed')) return { pct: 100, label: '✓ Report ready' };
    if (text.includes('generating pdf')) return { pct: 85, label: '📄 Generating PDF' };
    if (text.includes('valuation') || text.includes('dcf')) return { pct: 70, label: '🧮 Building valuation' };
    if (text.includes('news') || text.includes('catalyst')) return { pct: 55, label: '📰 News & catalysts' };
    if (text.includes('technical') || text.includes('indicator')) return { pct: 45, label: '📈 Technicals' };
    if (text.includes('fetch') || text.includes('fmp') || text.includes('market data')) return { pct: 30, label: '🔎 Fetching data' };
    if (text.includes('starting analysis')) return { pct: 15, label: '⚙️ Starting pipeline' };
    return { pct: 6, label: '⚙️ Queued' };
}

export default function DeepReports() {
    const { ticker } = useStore();
    const openaiKey = useVaultKey('openai');
    const [company, setCompany] = useState('');
    const [peers, setPeers] = useState('');
    const [busy, setBusy] = useState(false);
    const [state, setState] = useState<TaskState | null>(null);
    const [err, setErr] = useState('');
    const [elapsed, setElapsed] = useState(0);
    const logRef = useRef<HTMLDivElement>(null);
    const timer = useRef<ReturnType<typeof setInterval> | null>(null);
    const [engine, setEngine] = useState<'checking' | 'up' | 'down'>('checking');
    const setActiveTab = useStore((s) => s.setActiveTab);
    const setView = useStore((s) => s.setView);

    // Optional engine: probe it opaquely (no CORS on its root) before offering the form.
    useEffect(() => {
        let cancelled = false;
        fetch(FINROBOT, { mode: 'no-cors' })
            .then(() => !cancelled && setEngine('up'))
            .catch(() => !cancelled && setEngine('down'));
        return () => {
            cancelled = true;
        };
    }, []);

    // Pre-fill the company name for the terminal ticker.
    useEffect(() => {
        jget<{ name?: string }>(`${ANALYTICS_URL}/market/quote/${ticker}`)
            .then((q) => q.name && setCompany(q.name))
            .catch(() => {});
    }, [ticker]);

    useEffect(
        () => () => {
            if (timer.current) clearInterval(timer.current);
        },
        [],
    );
    useEffect(() => {
        // auto-scroll the streaming log
        if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, [state?.logs?.length]);

    const poll = (taskId: string) => {
        if (timer.current) clearInterval(timer.current);
        setElapsed(0);
        timer.current = setInterval(async () => {
            setElapsed((s) => s + 2);
            try {
                const r = await fetch(`${FINROBOT}/api/status/${taskId}`, { credentials: 'include' });
                if (!r.ok) return;
                const s: TaskState = await r.json();
                setState(s);
                if (s.status === 'completed' || s.status === 'failed') {
                    if (timer.current) clearInterval(timer.current);
                    setBusy(false);
                }
            } catch {
                /* keep polling */
            }
        }, 2000);
    };

    const generate = async () => {
        if (!company.trim()) {
            setErr('Enter the company name (e.g. Apple Inc.) to generate a report.');
            return;
        }
        if (!openaiKey) {
            setErr('The report engine writes with OpenAI — add an OpenAI key in the vault (🔑) first.');
            return;
        }
        setBusy(true);
        setErr('');
        setState({ status: 'pending', logs: [], result: null });
        try {
            const r = await fetch(`${FINROBOT}/api/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    ticker,
                    company_name: company.trim(),
                    peers: peers
                        .split(/[,\s]+/)
                        .map((p) => p.trim().toUpperCase())
                        .filter(Boolean),
                    openai_api_key: openaiKey,
                    generate_text: true,
                    generate_pdf: true,
                    enable_sensitivity_analysis: true,
                    enable_catalyst_analysis: true,
                    enable_enhanced_news: true,
                    enable_enhanced_charts: true,
                    enable_valuation_analysis: true,
                }),
            });
            if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
            const { task_id } = await r.json();
            poll(task_id);
        } catch (e) {
            setErr(String(e));
            setBusy(false);
        }
    };

    const report = state?.result;
    const reportUrl = report?.html?.length ? `${FINROBOT}/output/${report.ticker}/report/${report.html[0]}` : null;
    const pdfUrl = report?.pdf?.length ? `${FINROBOT}/output/${report.ticker}/report/${report.pdf[0]}` : null;

    return (
        <div className="animate-fade-in space-y-4">
            <div className="card p-5">
                <div className="mb-3 flex items-center gap-3">
                    <h2 className="section-heading">Deep Reports · {ticker}</h2>
                    <span className="badge-accent text-[10px]">⚡ Multi-agent equity research</span>
                </div>
                {engine === 'down' && (
                    <div className="mb-4 rounded-lg border border-white/10 p-4 text-sm text-white/60">
                        The multi-agent report engine isn&apos;t running on this machine (<code>./start-terminal.sh</code> starts it).
                        Aeon&apos;s own 55-dimension report for {ticker} is ready in the Research tab.
                        <button
                            className="btn-primary ml-3"
                            style={{ fontSize: 11 }}
                            onClick={() => {
                                setActiveTab('research');
                                setView('analysis');
                            }}
                        >
                            Open Research →
                        </button>
                    </div>
                )}
                <div className="flex flex-wrap items-end gap-2">
                    <div>
                        <label className="stat-label mb-1 block">Company name</label>
                        <input
                            className="input-field !w-[240px]"
                            value={company}
                            onChange={(e) => setCompany(e.target.value)}
                            placeholder="e.g. Apple Inc."
                            onKeyDown={(e) => e.key === 'Enter' && !busy && generate()}
                        />
                    </div>
                    <div>
                        <label className="stat-label mb-1 block">Peer tickers (optional)</label>
                        <input
                            className="input-field !w-[200px]"
                            value={peers}
                            onChange={(e) => setPeers(e.target.value)}
                            placeholder="e.g. MSFT, SAP, IBM"
                            onKeyDown={(e) => e.key === 'Enter' && !busy && generate()}
                        />
                    </div>
                    <button className="btn-primary" onClick={generate} disabled={busy}>
                        {busy ? 'Generating…' : `Generate report for ${ticker}`}
                    </button>
                    <VaultKeyStatus provider="openai" label="OpenAI" />
                </div>
                {err && <ErrorNote msg={err} />}
                <p className="mt-2 text-xs text-white/30">
                    A full institutional report runs a multi-agent pipeline — typically 1–3 minutes. Writes with OpenAI.
                </p>
            </div>

            {busy &&
                state &&
                state.status !== 'completed' &&
                (() => {
                    const { pct, label } = phaseFromLogs(state.logs ?? []);
                    // gentle time creep so the bar never looks frozen between phases
                    const shown = Math.min(pct + Math.min(elapsed / 8, 8), 97);
                    return (
                        <ProgressBar
                            pct={shown}
                            label={label}
                            sub={`Elapsed ${Math.floor(elapsed / 60)}m ${elapsed % 60}s · live pipeline log below · safe to switch tabs`}
                        />
                    );
                })()}

            {state && (state.status === 'failed' || (busy && state.status !== 'completed')) && (
                <div className="card-glass p-4">
                    <p className="stat-label mb-2 text-white/50">Pipeline log</p>
                    <div
                        ref={logRef}
                        className="max-h-56 overflow-y-auto rounded-lg bg-black/40 p-3 font-mono text-[11px] leading-relaxed text-white/60"
                    >
                        {(state.logs ?? []).map((l, i) => (
                            <div key={i} className={/error|failed|traceback|modulenotfound/i.test(l) ? 'text-rose' : ''}>
                                {l}
                            </div>
                        ))}
                        {(!state.logs || state.logs.length === 0) && <div className="text-white/30">Starting pipeline…</div>}
                    </div>
                    {state.status === 'failed' && (
                        <p className="mt-2 text-sm text-rose">
                            The report pipeline failed — see the log above. Most often this means the OpenAI key was rejected or hit a
                            limit.
                        </p>
                    )}
                </div>
            )}

            {reportUrl && (
                <div>
                    <div className="mb-2 flex items-center gap-3">
                        <span className="badge-success text-[10px]">✓ Report ready</span>
                        {pdfUrl && (
                            <a className="btn-secondary !py-1 !px-3 text-xs" href={pdfUrl} target="_blank" rel="noreferrer">
                                ⬇ Download PDF
                            </a>
                        )}
                    </div>
                    <div className="overflow-hidden rounded-2xl border border-white/[0.06]" style={{ background: '#fff' }}>
                        <iframe src={reportUrl} title="Equity research report" className="h-[78vh] w-full" />
                    </div>
                </div>
            )}
        </div>
    );
}
