/**
 * About / Licenses — the professional way a finished product carries its
 * open-source notices: one tidy screen (like Settings → Legal in any
 * commercial app), not scattered credits. Reachable from the command
 * palette and the footer.
 */
import { AeonMark } from '../App';
import { DATA_SOURCES } from '../dataProvenance';

// Only the licensed, real engines get an attribution row here — the
// Aeon-native (mock/approximation) entries in the registry are for
// SourceBadge only and have no license to credit.
const ENGINES = DATA_SOURCES.filter((s) => s.license);

export default function About() {
    return (
        <div className="mx-auto max-w-3xl animate-fade-in space-y-6">
            <div className="text-center">
                <div
                    className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl"
                    style={{ background: 'rgba(0,200,255,0.06)' }}
                >
                    <AeonMark size={38} />
                </div>
                <h1 className="font-display text-3xl font-black">
                    <span className="text-gradient-hero">Aeon Nimbus</span> <span className="text-gradient">Analysis</span>
                </h1>
                <p className="mt-2 text-sm text-white/50">
                    A unified financial workstation — one ticker, every engine, entirely on your machine.
                </p>
            </div>

            <div className="card p-6">
                <h2 className="section-heading mb-4">Built on open foundations</h2>
                <p className="mb-4 max-w-2xl text-sm leading-relaxed text-white/60">
                    The Aeon Nimbus experience — the Fusion valuation ensemble, the Council of Agents, the unified terminal, and the report
                    engine — is original work. Several data and analysis engines underneath are open-source projects, each used under its
                    own license and credited here.
                </p>
                <div className="overflow-hidden rounded-xl border border-white/[0.06]">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/[0.06] bg-white/[0.02] text-left text-[10px] uppercase tracking-wider text-white/40">
                                <th className="px-4 py-2.5">Engine</th>
                                <th className="px-4 py-2.5">Role</th>
                                <th className="px-4 py-2.5">License</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ENGINES.map((e) => (
                                <tr key={e.id} className="border-b border-white/[0.03] last:border-0">
                                    <td className="px-4 py-2.5 font-semibold text-white/85">{e.engineName ?? e.label}</td>
                                    <td className="px-4 py-2.5 text-white/50">{e.role}</td>
                                    <td className="px-4 py-2.5">
                                        <span className="badge-accent text-[10px]">{e.license}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <p className="mt-4 text-xs leading-relaxed text-white/35">
                    Full license texts ship with the source in each engine's directory. AGPL-3.0 components require that the corresponding
                    source be made available to anyone you distribute this to.
                </p>
            </div>

            <div className="card-glass p-5 text-center">
                <p className="text-xs tracking-wider text-white/30">
                    Everything runs locally · Not financial advice · Always do your own research
                </p>
            </div>
        </div>
    );
}
