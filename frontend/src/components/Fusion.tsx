/**
 * Fusion — the overlap across all five vendored projects turned into
 * original ensemble features instead of picking one winner:
 *   Valuation Ensemble  — 5 valuation philosophies vote; disagreement quantified
 *   Source Integrity    — redundant fetchers become cross-verification
 *   Council of Agents   — every agent paradigm deliberates; chair synthesizes
 */
import { useEffect, useRef, useState } from 'react';
import { ErrorNote, humanizeErr, ProgressBar, useVaultKey, VaultKeyStatus } from './Terminal';
import { useStore } from '../store';
import { jget, jpost } from '../utils/api';

const AEON = 'http://127.0.0.1:8000';

type Ensemble = {
    price: number; consensus: number; consensusUpside: number;
    disagreementIndex: number; readout: string;
    models: Record<string, { value: number; philosophy: string; upside: number }>;
};
type Integrity = {
    sources: Record<string, number>; spreadBps?: number;
    verified: boolean | null; note: string;
};
type CouncilJob = {
    status: 'running' | 'done' | 'error'; phase?: string; progress?: number; error?: string;
    seats?: { seat: string; label: string; text: string; vote: string }[];
    tally?: Record<string, number>; agreement?: number;
    verdict?: string; chairRuling?: string;
};

const MODEL_ICONS: Record<string, string> = {
    dcf: '🌊', graham: '📚', lynch: '🛒', analysts: '🏦', montecarlo: '🎲',
};
const VOTE_CLS: Record<string, string> = {
    BUY: 'text-emerald', HOLD: 'text-gold-light', SELL: 'text-rose',
};

export default function FusionTab() {
    const { ticker } = useStore();
    const [ens, setEns] = useState<Ensemble | null>(null);
    const [integ, setInteg] = useState<Integrity | null>(null);
    const [err, setErr] = useState('');

    // Council state — key comes from the shared vault (🔑 Manage Keys)
    const key = useVaultKey('gemini');
    const [deep, setDeep] = useState(false);
    const [job, setJob] = useState<CouncilJob | null>(null);
    const [busy, setBusy] = useState(false);
    const timer = useRef<ReturnType<typeof setInterval> | null>(null);

    useEffect(() => {
        setEns(null); setInteg(null); setErr('');
        jget<Ensemble>(`${AEON}/fusion/valuation/${ticker}`).then(setEns)
            .catch((e) => setErr(String(e)));
        jget<Integrity>(`${AEON}/fusion/quote/${ticker}`).then(setInteg).catch(() => {});
    }, [ticker]);

    const poll = (jobId: string) => {
        if (timer.current) clearInterval(timer.current);
        timer.current = setInterval(async () => {
            try {
                const j = await jget<CouncilJob>(`${AEON}/fusion/council/${jobId}`);
                setJob(j);
                if (j.status !== 'running') {
                    if (timer.current) clearInterval(timer.current);
                    setBusy(false);
                    localStorage.removeItem('aeonnimbus_council_job');
                }
            } catch { /* keep polling */ }
        }, 4000);
    };

    const convene = async () => {
        if (!key) { setErr('The council needs a Gemini key — every seat is a real LLM run.'); return; }
        setBusy(true); setJob(null); setErr('');
        try {
            const { jobId } = await jpost<{ jobId: string }>(`${AEON}/fusion/council`,
                { ticker, geminiKey: key, includeDebate: deep });
            // Stored with its ticker (not just the jobId) so other tabs — e.g.
            // Alpha Digest — can tell whether a cached job matches their ticker.
            localStorage.setItem('aeonnimbus_council_job', JSON.stringify({ jobId, ticker }));
            poll(jobId);
        } catch (e) { setErr(String(e)); setBusy(false); }
    };

    // Resume a council that was convened before a tab switch or reload
    useEffect(() => {
        const raw = localStorage.getItem('aeonnimbus_council_job');
        if (raw) {
            try {
                const { jobId } = JSON.parse(raw);
                if (jobId) { setBusy(true); poll(jobId); }
            } catch { localStorage.removeItem('aeonnimbus_council_job'); }
        }
        return () => { if (timer.current) clearInterval(timer.current); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Bar positions for the ensemble chart
    const spread = ens ? Object.values(ens.models).map((m) => m.value) : [];
    const lo = Math.min(...spread, ens?.price ?? Infinity);
    const hi = Math.max(...spread, ens?.price ?? 0);
    const pos = (v: number) => hi === lo ? 50 : ((v - lo) / (hi - lo)) * 92 + 4;

    return (
        <div className="animate-fade-in space-y-4">
            {/* ── Valuation Ensemble ── */}
            <div className="card p-5">
                <div className="mb-1 flex flex-wrap items-center gap-3">
                    <h2 className="section-heading">Valuation Ensemble · {ticker}</h2>
                    <span className="badge-nebula">5 philosophies, 1 vote</span>
                </div>
                <p className="mb-4 text-xs text-white/40">
                    Every valuation approach in the terminal — DCF, Graham, Lynch, street targets,
                    stochastic simulation — votes independently. Where they agree, trust rises; where they
                    diverge, the spread itself is the finding.
                </p>
                {err && !ens && <ErrorNote msg={err} />}
                {ens && (
                    <>
                        <div className="relative mb-6 mt-8 h-14">
                            {/* price marker */}
                            <div className="absolute top-0 h-full w-[2px] bg-white/60" style={{ left: `${pos(ens.price)}%` }}>
                                <span className="absolute -top-6 -translate-x-1/2 font-mono text-xs text-white">${ens.price}</span>
                            </div>
                            {/* consensus marker */}
                            <div className="absolute top-0 h-full w-[2px] bg-accent" style={{ left: `${pos(ens.consensus)}%` }}>
                                <span className="absolute -bottom-6 -translate-x-1/2 whitespace-nowrap font-mono text-xs text-accent">consensus ${ens.consensus}</span>
                            </div>
                            {/* model dots */}
                            {Object.entries(ens.models).map(([k, m]) => (
                                <div key={k} className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 text-xl"
                                    style={{ left: `${pos(m.value)}%` }} title={`${k}: $${m.value}`}>
                                    {MODEL_ICONS[k] ?? '●'}
                                </div>
                            ))}
                            <div className="absolute top-1/2 h-[1px] w-full bg-white/10" />
                        </div>
                        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                            {Object.entries(ens.models).map(([k, m]) => (
                                <div key={k} className="card-glass flex items-center justify-between p-3">
                                    <div>
                                        <p className="text-sm font-semibold text-white/80">{MODEL_ICONS[k]} {k}</p>
                                        <p className="text-[10px] text-white/40">{m.philosophy}</p>
                                    </div>
                                    <p className={`font-mono text-sm font-bold ${m.upside >= 0 ? 'text-emerald' : 'text-rose'}`}>
                                        ${m.value}
                                    </p>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 card-cyan p-4">
                            <p className="text-sm text-white/80">
                                <span className="font-mono font-bold text-accent">Disagreement index {ens.disagreementIndex}%</span> — {ens.readout}.
                                Ensemble consensus <span className="font-mono">${ens.consensus}</span> ({ens.consensusUpside > 0 ? '+' : ''}{ens.consensusUpside}% vs price).
                            </p>
                        </div>
                    </>
                )}
                {/* Source integrity strip */}
                {integ && (
                    <p className="mt-3 text-xs text-white/40">
                        🔍 Source cross-check: {Object.entries(integ.sources).map(([s, v]) => `${s} $${v}`).join(' · ')}
                        {' — '}
                        <span className={integ.verified ? 'text-emerald' : integ.verified === false ? 'text-rose' : 'text-white/40'}>
                            {integ.note}{integ.spreadBps != null && ` (${integ.spreadBps} bps)`}
                        </span>
                    </p>
                )}
            </div>

            {/* ── Council of Agents ── */}
            <div className="card-premium p-5">
                <div className="mb-1 flex flex-wrap items-center gap-3">
                    <h2 className="section-heading">Council of Agents · {ticker}</h2>
                    <span className="badge-nebula">all paradigms, one table</span>
                </div>
                <p className="mb-3 text-xs text-white/40">
                    A market analyst, a specialist research hierarchy, classic investor personas —
                    and optionally the full multi-agent debate — each take a seat.
                    Votes are tallied, agreement measured, and a chair synthesizes the ruling.
                </p>
                <div className="flex flex-wrap items-center gap-3">
                    <button className="btn-nebula" onClick={convene} disabled={busy}>
                        {busy ? 'Council in session…' : `Convene council on ${ticker}`}
                    </button>
                    <label className="flex items-center gap-2 text-xs text-white/60">
                        <input type="checkbox" checked={deep} onChange={(e) => setDeep(e.target.checked)} />
                        include full multi-agent debate (+3–10 min)
                    </label>
                    <VaultKeyStatus provider="gemini" label="Gemini" />
                </div>
                {err && ens && <ErrorNote msg={err} />}
                {busy && (
                    <ProgressBar
                        pct={(job?.progress ?? 0) * 100}
                        label={job?.phase ?? 'Convening the seats…'}
                        sub="Live phase reported by the council. Calls are paced ~7s apart to respect free-tier rate limits (~1-2 min total; +3-10 min with the debate seat). Safe to switch tabs."
                    />
                )}
                {job?.status === 'error' && <p className="mt-3 max-w-2xl text-sm leading-relaxed text-rose">{humanizeErr(job.error ?? '')}</p>}
                {job?.status === 'done' && job.seats && (
                    <div className="mt-5 space-y-3">
                        <div className="flex flex-wrap items-center gap-4">
                            <div className="font-display text-3xl font-black">
                                <span className={VOTE_CLS[job.verdict ?? 'HOLD']}>{job.verdict}</span>
                            </div>
                            <div className="flex gap-2">
                                {Object.entries(job.tally ?? {}).map(([v, n]) => n > 0 && (
                                    <span key={v} className="badge-accent">{v} × {n}</span>
                                ))}
                            </div>
                            <span className="text-xs text-white/50">seat agreement {job.agreement}%</span>
                        </div>
                        <div className="card-cyan p-4">
                            <p className="stat-label mb-1 text-accent">Chair's ruling</p>
                            <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/85">{job.chairRuling}</p>
                        </div>
                        <div className="grid gap-3 lg:grid-cols-2">
                            {job.seats.map((s) => (
                                <details key={s.seat} className="card-glass p-4">
                                    <summary className="cursor-pointer text-sm">
                                        <span className="stat-label">{s.label}</span>
                                        <span className={`ml-2 font-mono font-bold ${VOTE_CLS[s.vote]}`}>{s.vote}</span>
                                    </summary>
                                    <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-white/75">{s.text}</p>
                                </details>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
