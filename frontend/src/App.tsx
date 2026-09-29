import { lazy, Suspense, useEffect, useState } from 'react';
import { useStore } from './store';
import KeyVault from './components/KeyVault';
import AnalysisForm from './components/AnalysisForm';
import ErrorBoundary from './components/ErrorBoundary';
import { MarketsTab, AgentDeskTab, OverviewTab, ServiceStatus } from './components/Terminal';
import FusionTab from './components/Fusion';
import HoustonTab from './components/Houston';
import CommandPalette from './components/CommandPalette';
import About from './components/About';
import DeepReports from './components/DeepReports';
import DeepResearch from './components/DeepResearch';
import Onboarding from './components/Onboarding';
import AlertsManager from './components/AlertsManager';
import ComparisonView from './components/ComparisonView';
import AnalysisHistory from './components/AnalysisHistory';
import WatchlistManager from './components/WatchlistManager';
import RumorNewsTiming from './components/RumorNewsTiming';
import AlphaDigest from './components/AlphaDigest';

const ReportViewer = lazy(() => import('./components/ReportViewer'));

const TABS = [
    ['overview', 'Overview'],
    ['fusion', 'Fusion'],
    ['digest', 'Alpha Digest'],
    ['research', 'Research'],
    ['finrobot', 'Reports'],
    ['analyst', 'Deep Research'],
    ['markets', 'Markets'],
    ['agents', 'Agents'],
    ['houston', 'Houston'],
    ['compare', 'Compare'],
    ['alerts', 'Alerts'],
    ['history', 'History'],
    ['watchlist', 'Watchlist'],
    ['rumor', 'Rumor/News'],
] as const;
type Tab = (typeof TABS)[number][0];

const TAB_GROUPS: { label: string; ids: Tab[] }[] = [
    { label: 'Command', ids: ['overview', 'fusion', 'digest'] },
    { label: 'Research', ids: ['research', 'finrobot', 'analyst'] },
    { label: 'Markets', ids: ['markets', 'agents', 'rumor'] },
    { label: 'Tools', ids: ['compare', 'alerts', 'history', 'watchlist'] },
    { label: 'Ops', ids: ['houston'] },
];
const TAB_LABEL: Record<Tab, string> = Object.fromEntries(TABS) as Record<Tab, string>;

export default function App() {
    const { view } = useStore();
    const tab = useStore((s) => s.activeTab);
    const setActiveTab = useStore((s) => s.setActiveTab);
    const setTab = (t: Tab) => setActiveTab(t);

    useEffect(() => {
        const name = TAB_LABEL[tab as Tab] ?? (tab === 'about' ? 'About' : 'Terminal');
        document.title = `${name} — Aeon Analysis`;
    }, [tab]);

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if (e.key === '/' && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement)) {
                e.preventDefault();
                document.getElementById('global-ticker-input')?.focus();
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, []);

    return (
        <ErrorBoundary>
            <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--ink)' }}>
                <Onboarding />
                <AlertsManager />
                <CommandPalette tabs={TABS.map(([id]) => ({ id, label: TAB_LABEL[id] }))} />
                <Nav />
                {/* Tab bar */}
                <div style={{ borderBottom: '1px solid var(--rule2)' }}>
                    <div className="mx-auto max-w-7xl px-6">
                        <div className="flex items-center gap-0 overflow-x-auto">
                            {TAB_GROUPS.map((group, gi) => (
                                <div key={group.label} className="flex items-center">
                                    {gi > 0 && (
                                        <span
                                            style={{ width: 1, height: 14, background: 'var(--rule2)', margin: '0 12px', flexShrink: 0 }}
                                        />
                                    )}
                                    {group.ids.map((id) => (
                                        <button
                                            key={id}
                                            onClick={() => setTab(id)}
                                            style={{
                                                padding: '9px 14px',
                                                margin: '6px 1px',
                                                fontFamily: '"JetBrains Mono", monospace',
                                                fontSize: '11px',
                                                fontWeight: 500,
                                                letterSpacing: '0.05em',
                                                textTransform: 'uppercase',
                                                whiteSpace: 'nowrap',
                                                border: '1px solid transparent',
                                                borderRadius: '8px',
                                                background: tab === id ? 'rgba(212,175,55,0.10)' : 'transparent',
                                                borderColor: tab === id ? 'var(--goldrl)' : 'transparent',
                                                color: tab === id ? 'var(--gold2)' : 'var(--ink3)',
                                                cursor: 'pointer',
                                                transition: 'color 0.15s, background 0.15s, border-color 0.15s',
                                            }}
                                            onMouseEnter={(e) => {
                                                if (tab !== id) {
                                                    (e.target as HTMLElement).style.color = 'var(--ink2)';
                                                    (e.target as HTMLElement).style.background = 'rgba(255,255,255,0.04)';
                                                }
                                            }}
                                            onMouseLeave={(e) => {
                                                if (tab !== id) {
                                                    (e.target as HTMLElement).style.color = 'var(--ink3)';
                                                    (e.target as HTMLElement).style.background = 'transparent';
                                                }
                                            }}
                                        >
                                            {TAB_LABEL[id]}
                                        </button>
                                    ))}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
                <main className="mx-auto max-w-7xl px-6 py-6">
                    {tab === 'overview' && (
                        <ErrorBoundary>
                            <OverviewTab goTo={(t) => setTab(t as Tab)} />
                        </ErrorBoundary>
                    )}
                    {tab === 'fusion' && (
                        <ErrorBoundary>
                            <FusionTab />
                        </ErrorBoundary>
                    )}
                    {tab === 'digest' && (
                        <ErrorBoundary>
                            <AlphaDigest />
                        </ErrorBoundary>
                    )}
                    {tab === 'markets' && (
                        <ErrorBoundary>
                            <MarketsTab />
                        </ErrorBoundary>
                    )}
                    {tab === 'agents' && (
                        <ErrorBoundary>
                            <AgentDeskTab />
                        </ErrorBoundary>
                    )}
                    {tab === 'finrobot' && (
                        <ErrorBoundary>
                            <DeepReports />
                        </ErrorBoundary>
                    )}
                    {tab === 'analyst' && (
                        <ErrorBoundary>
                            <DeepResearch />
                        </ErrorBoundary>
                    )}
                    {tab === 'houston' && (
                        <ErrorBoundary>
                            <HoustonTab />
                        </ErrorBoundary>
                    )}
                    {tab === 'compare' && (
                        <ErrorBoundary>
                            <ComparisonView />
                        </ErrorBoundary>
                    )}
                    {tab === 'alerts' && (
                        <ErrorBoundary>
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold" style={{ color: 'var(--gold)' }}>
                                    Alert Manager
                                </h2>
                                <p style={{ color: 'var(--ink2)' }}>Alerts run in background. Configure below.</p>
                            </div>
                        </ErrorBoundary>
                    )}
                    {tab === 'history' && (
                        <ErrorBoundary>
                            <AnalysisHistory />
                        </ErrorBoundary>
                    )}
                    {tab === 'watchlist' && (
                        <ErrorBoundary>
                            <WatchlistManager />
                        </ErrorBoundary>
                    )}
                    {tab === 'rumor' && (
                        <ErrorBoundary>
                            <RumorNewsTiming />
                        </ErrorBoundary>
                    )}
                    {tab === 'about' && (
                        <ErrorBoundary>
                            <About />
                        </ErrorBoundary>
                    )}
                    {tab === 'research' && view === 'setup' && <ResearchLanding />}
                    {tab === 'research' && view === 'analysis' && <AnalysisForm />}
                    {tab === 'research' && view === 'report' && (
                        <Suspense
                            fallback={
                                <div
                                    style={{
                                        padding: '80px 0',
                                        textAlign: 'center',
                                        fontFamily: '"JetBrains Mono", monospace',
                                        fontSize: 12,
                                        color: 'var(--ink3)',
                                    }}
                                >
                                    Loading report…
                                </div>
                            }
                        >
                            <ErrorBoundary>
                                <ReportViewer />
                            </ErrorBoundary>
                        </Suspense>
                    )}
                </main>
                <Footer />
            </div>
        </ErrorBoundary>
    );
}

function Nav() {
    const { view, setView, clearResult } = useStore();
    const setActiveTab = useStore((s) => s.setActiveTab);

    return (
        <nav
            style={{
                position: 'sticky',
                top: 0,
                zIndex: 50,
                background: 'rgba(4,4,8,0.97)',
                borderBottom: '1px solid var(--rule2)',
                backdropFilter: 'blur(16px)',
            }}
        >
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
                <button
                    onClick={() => {
                        clearResult();
                        setView('setup');
                        setActiveTab('overview');
                    }}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        padding: 0,
                    }}
                    id="nav-logo"
                >
                    <AeonMark size={24} />
                    <span
                        style={{
                            fontFamily: 'Inter, -apple-system, sans-serif',
                            fontSize: 16,
                            fontWeight: 700,
                            color: 'var(--ink)',
                            letterSpacing: '-0.02em',
                        }}
                    >
                        Aeon Nimbus <span style={{ color: 'var(--gold)' }}>Analysis</span>
                    </span>
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <ServiceStatus />
                    <GlobalTickerSearch />
                    <kbd
                        style={{
                            display: 'none',
                            padding: '2px 6px',
                            borderRadius: 2,
                            border: '1px solid var(--rule2)',
                            fontFamily: '"JetBrains Mono", monospace',
                            fontSize: 10,
                            color: 'var(--ink3)',
                        }}
                        className="sm:inline-block"
                        title="Command palette"
                    >
                        ⌘K
                    </kbd>
                    {view === 'report' && <span className="badge-gold">REPORT</span>}
                    <button
                        onClick={() => {
                            setView('setup');
                            setActiveTab('research');
                        }}
                        className="btn-secondary"
                        style={{ fontSize: 11 }}
                        id="nav-manage-keys"
                        title="API key vault"
                    >
                        Keys
                    </button>
                </div>
            </div>
        </nav>
    );
}

export function AeonMark({ size = 24 }: { size?: number }) {
    return (
        <svg width={size} height={size} viewBox="0 0 32 32" aria-label="Aeon Nimbus" fill="none">
            <path d="M16 4.5a11.5 11.5 0 1 0 11.5 11.5" stroke="#D4AF37" strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="27.5" cy="16" r="2.2" fill="#F0CF5C" />
            <circle cx="16" cy="16" r="3.8" fill="#D4AF37" />
        </svg>
    );
}

function GlobalTickerSearch() {
    const { ticker, setTicker } = useStore();
    const [v, setV] = useState(ticker);
    useEffect(() => setV(ticker), [ticker]);
    return (
        <form
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            onSubmit={(e) => {
                e.preventDefault();
                setTicker(v);
            }}
        >
            <input
                id="global-ticker-input"
                className="input-field"
                style={{ width: 90, textAlign: 'center', textTransform: 'uppercase', padding: '5px 10px', fontSize: 12 }}
                value={v}
                onChange={(e) => setV(e.target.value)}
                title='Global ticker — press "/" to focus'
            />
            <button className="btn-primary" style={{ padding: '5px 12px', fontSize: 11 }}>
                Set
            </button>
        </form>
    );
}

/* Research tab landing — functional, not a marketing brochure */
function ResearchLanding() {
    const { setView } = useStore();
    return (
        <div className="animate-fade-in" style={{ maxWidth: 640, margin: '0 auto', padding: '48px 0' }}>
            <p className="section-heading" style={{ marginBottom: 12 }}>
                Research Engine
            </p>
            <h1
                style={{
                    fontFamily: 'Inter, -apple-system, sans-serif',
                    fontSize: '2rem',
                    fontWeight: 700,
                    letterSpacing: '-0.03em',
                    color: 'var(--ink)',
                    marginBottom: 8,
                }}
            >
                55 dimensions. Three valuation models.
            </h1>
            <p style={{ color: 'var(--ink2)', fontSize: 14, lineHeight: 1.7, marginBottom: 32 }}>
                Full stock report generated in seconds. DCF, Graham Number, Peter Lynch. Bull/base/bear scenarios with probabilities. Runs
                entirely on your machine.
            </p>
            <button className="btn-primary" onClick={() => setView('analysis')}>
                Run analysis →
            </button>
            <div style={{ marginTop: 48, borderTop: '1px solid var(--rule2)', paddingTop: 32 }}>
                <KeyVault />
            </div>
        </div>
    );
}

function Footer() {
    const setActiveTab = useStore((s) => s.setActiveTab);
    return (
        <footer style={{ marginTop: 64, borderTop: '1px solid var(--rule2)', padding: '24px 0', textAlign: 'center' }}>
            <p
                style={{
                    fontFamily: '"JetBrains Mono", monospace',
                    fontSize: 10,
                    letterSpacing: '0.08em',
                    color: 'var(--ink3)',
                    textTransform: 'uppercase',
                }}
            >
                Aeon Nimbus Analysis — runs on your machine · not financial advice
            </p>
            <button
                onClick={() => setActiveTab('about')}
                style={{
                    marginTop: 6,
                    fontFamily: '"JetBrains Mono", monospace',
                    fontSize: 10,
                    color: 'var(--ink3)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'color 0.15s',
                }}
                onMouseEnter={(e) => ((e.target as HTMLElement).style.color = 'var(--gold)')}
                onMouseLeave={(e) => ((e.target as HTMLElement).style.color = 'var(--ink3)')}
            >
                Licences
            </button>
        </footer>
    );
}
