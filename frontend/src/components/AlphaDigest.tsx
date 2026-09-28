/**
 * Alpha Digest — one ticker, every already-real signal, one page.
 * Aeon Analysis's methodology upgrades (CAPM DCF, grounded personas, the
 * honest Fusion ensemble/council) are real but scattered across 5+ tabs the
 * user has to flip between and reconcile by hand. This assembles them into
 * one view without inventing a new methodology or blending sources into a
 * false single number — each section keeps its own provenance/methodology
 * string visible, matching the standard set by dataProvenance.ts.
 */
import { useEffect, useState } from 'react';
import { useStore } from '../store';
import { jget, jpost } from '../utils/api';
import { ErrorNote, VaultKeyStatus, SourceBadge } from './Terminal';
import { SectionCard } from './report/shared';

const AEON = 'http://127.0.0.1:8000';

type DcfResp = {
    price: number; wacc: number; terminalGrowth: number; methodology: string;
    scenarios: Record<'bear' | 'base' | 'bull', { growth: number; fairValue: number; upside: number }>;
};
type Ensemble = {
    price: number; consensus: number; consensusUpside: number;
    disagreementIndex: number; readout: string;
    models: Record<string, { value: number; philosophy: string; upside: number }>;
};
type Personas = { mode: string; analyses: { persona: string; text: string }[] };
type Gate = { ticker: string; file: string; entry?: string; target?: string; stop?: string; size?: string; kill?: string; };
type CouncilJob = {
    status: 'running' | 'done' | 'error'; verdict?: string; chairRuling?: string;
    agreement?: number; tally?: Record<string, number>; error?: string;
};

const PERSONA_LABEL: Record<string, string> = {
    buffett: '🏛️ Buffett', graham: '📚 Graham', lynch: '🛒 Lynch', munger: '🧠 Munger', marks: '🌊 Marks',
};
const VOTE_CLS: Record<string, string> = { BUY: 'text-emerald', HOLD: 'text-gold-light', SELL: 'text-rose' };

export default function AlphaDigest() {
    const { ticker } = useStore();
    const setActiveTab = useStore((s) => s.setActiveTab);

    const [dcf, setDcf] = useState<DcfResp | null>(null);
    const [dcfErr, setDcfErr] = useState('');
    const [ens, setEns] = useState<Ensemble | null>(null);
    const [ensErr, setEnsErr] = useState('');
    const [personas, setPersonas] = useState<Personas | null>(null);
    const [personasErr, setPersonasErr] = useState('');
    const [gate, setGate] = useState<Gate | null | undefined>(undefined); // undefined = loading
    const [gateErr, setGateErr] = useState('');
    const [council, setCouncil] = useState<CouncilJob | null>(null);

    useEffect(() => {
        setDcf(null); setDcfErr('');
        jget<DcfResp>(`${AEON}/quant/dcf/${ticker}`).then(setDcf).catch((e) => setDcfErr(String(e)));

        setEns(null); setEnsErr('');
        jget<Ensemble>(`${AEON}/fusion/valuation/${ticker}`).then(setEns).catch((e) => setEnsErr(String(e)));

        setPersonas(null); setPersonasErr('');
        jpost<Personas>(`${AEON}/agents/personas`, { ticker, personas: ['buffett', 'graham', 'lynch'], geminiKey: null })
            .then(setPersonas).catch((e) => setPersonasErr(String(e)));

        setGate(undefined); setGateErr('');
        jget<{ gates: Gate[] }>(`${AEON}/houston/gates`)
            .then((d) => setGate(d.gates.find((g) => g.ticker === ticker) ?? null))
            .catch((e) => { setGateErr(String(e)); setGate(null); });
    }, [ticker]);

    // Council is a multi-minute LLM job (Fusion tab) — the digest shows a
    // cached result rather than kicking one off, so opening this page never
    // silently spends Gemini quota. Fusion.tsx stores {jobId, ticker} in
    // localStorage precisely so this can verify the cached job is actually
    // for the ticker being viewed here, not a stale run for a different one.
    useEffect(() => {
        setCouncil(null);
        const raw = localStorage.getItem('aeonnimbus_council_job');
        if (!raw) return;
        try {
            const { jobId, ticker: jobTicker } = JSON.parse(raw);
            if (!jobId || jobTicker !== ticker) return;
            jget<CouncilJob>(`${AEON}/fusion/council/${jobId}`).then(setCouncil).catch(() => {});
        } catch { /* malformed cache entry — nothing to show */ }
    }, [ticker]);

    return (
        <div className="animate-fade-in space-y-4">
            <div>
                <h2 className="section-heading">Alpha Digest · {ticker}</h2>
                <p className="mt-1 text-xs text-white/40">
                    Every already-real signal in Aeon Analysis for one ticker, side by side — not a new
                    model, just synthesis. Each card names its own methodology; nothing here is blended
                    into a single number.
                </p>
            </div>

            {/* ── Valuation Ensemble (Fusion) ── */}
            <SectionCard title="Valuation Ensemble" icon="🌊">
                {ensErr && !ens && <ErrorNote msg={ensErr} />}
                {ens && (
                    <>
                        <p className="mb-3 text-sm text-white/80">
                            Consensus <span className="font-mono font-bold text-accent">${ens.consensus}</span>
                            {' '}({ens.consensusUpside > 0 ? '+' : ''}{ens.consensusUpside}% vs ${ens.price}) ·{' '}
                            <span className="font-mono">{ens.disagreementIndex}% disagreement</span> — {ens.readout}
                        </p>
                        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                            {Object.entries(ens.models).map(([k, m]) => (
                                <div key={k} className="card-glass p-3">
                                    <p className="text-sm font-semibold text-white/80">{k} — ${m.value}</p>
                                    <p className="text-[10px] text-white/40">{m.philosophy}</p>
                                </div>
                            ))}
                        </div>
                    </>
                )}
                <p className="mt-3 text-[10px] text-white/30">Full ensemble chart and re-run controls live in the Fusion tab.</p>
            </SectionCard>

            {/* ── CAPM DCF ── */}
            <SectionCard title="CAPM DCF" icon="📐">
                {dcfErr && <ErrorNote msg={dcfErr} />}
                {dcf && (
                    <>
                        <p className="mb-3 text-xs text-white/40">{dcf.methodology}</p>
                        <div className="grid gap-2 sm:grid-cols-3">
                            {(['bear', 'base', 'bull'] as const).map((s) => (
                                <div key={s} className="card-glass p-3">
                                    <p className="stat-label mb-1 capitalize">{s}</p>
                                    <p className="font-mono text-sm font-bold text-white/85">${dcf.scenarios[s].fairValue}</p>
                                    <p className={`text-xs ${dcf.scenarios[s].upside >= 0 ? 'text-emerald' : 'text-rose'}`}>
                                        {dcf.scenarios[s].upside > 0 ? '+' : ''}{dcf.scenarios[s].upside}% · growth {(dcf.scenarios[s].growth * 100).toFixed(1)}%
                                    </p>
                                </div>
                            ))}
                        </div>
                        <p className="mt-3 text-[10px] text-white/30">WACC {(dcf.wacc * 100).toFixed(1)}% · terminal growth {(dcf.terminalGrowth * 100).toFixed(1)}%</p>
                    </>
                )}
            </SectionCard>

            {/* ── Persona Verdicts ── */}
            <SectionCard title="Persona Verdicts" icon="🎭">
                <div className="mb-2 flex items-center gap-2">
                    <SourceBadge id="personas-native" />
                </div>
                {personasErr && <ErrorNote msg={personasErr} />}
                {personas && (
                    <div className="grid gap-3 sm:grid-cols-2">
                        {personas.mode === 'demo' && <span className="badge-gold sm:col-span-2">Quick take (free) — live AI available in the Personas tab</span>}
                        {personas.analyses.map((a) => (
                            <div key={a.persona} className="card-premium p-4">
                                <p className="stat-label mb-1">{PERSONA_LABEL[a.persona] ?? a.persona}</p>
                                <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/80">{a.text}</p>
                            </div>
                        ))}
                    </div>
                )}
            </SectionCard>

            {/* ── Houston Thesis Gate ── */}
            <SectionCard title="Thesis Gate" icon="🛡">
                {gateErr && <ErrorNote msg={gateErr} />}
                {gate === null && (
                    <p className="text-sm text-white/50">
                        No thesis gate on file for {ticker}. Write one in{' '}
                        <button className="text-accent underline" onClick={() => setActiveTab('houston')}>Houston</button>{' '}
                        before sizing a position.
                    </p>
                )}
                {gate && (
                    <div>
                        <div className="mb-2 flex flex-wrap gap-3 text-sm">
                            {gate.entry && <span>Entry {gate.entry}</span>}
                            {gate.target && <span className="text-emerald">→ {gate.target}</span>}
                            {gate.stop && <span className="text-rose">Stop {gate.stop}</span>}
                            {gate.size && <span className="text-white/50">| {gate.size}</span>}
                        </div>
                        {gate.kill && <p className="text-xs leading-relaxed text-gold-light"><b>Kill: </b>{gate.kill}</p>}
                    </div>
                )}
            </SectionCard>

            {/* ── Council of Agents (cached) ── */}
            <SectionCard title="Council of Agents" icon="⚖️">
                {!council && (
                    <div className="flex items-center gap-3">
                        <p className="text-sm text-white/50">No council run cached yet — every seat is a real LLM run, so it's convened manually.</p>
                        <button className="btn-nebula" onClick={() => setActiveTab('fusion')}>Convene in Fusion →</button>
                        <VaultKeyStatus provider="gemini" label="Gemini" />
                    </div>
                )}
                {council?.status === 'running' && <p className="text-sm text-white/50">A council is still deliberating — check the Fusion tab.</p>}
                {council?.status === 'error' && <ErrorNote msg={council.error ?? 'Council run failed.'} />}
                {council?.status === 'done' && (
                    <div>
                        <div className="mb-2 flex flex-wrap items-center gap-3">
                            <span className={`font-display text-2xl font-black ${VOTE_CLS[council.verdict ?? 'HOLD']}`}>{council.verdict}</span>
                            <span className="text-xs text-white/50">seat agreement {council.agreement}%</span>
                        </div>
                        <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/80">{council.chairRuling}</p>
                    </div>
                )}
            </SectionCard>
        </div>
    );
}
