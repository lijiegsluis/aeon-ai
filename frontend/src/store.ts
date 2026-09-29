import { create } from 'zustand';
import type { APIKeys } from './utils/crypto';
import { encryptCache, decryptCache, migrateLegacyKeys } from './utils/crypto';

/**
 * Re-export all shared types so existing component imports
 * (`import type { AnalysisResponse } from '../store'`) keep working.
 */
export type {
    AnalysisResponse,
    ResearchSources,
    FinancialData,
    TechnicalAnalysis,
    InsiderActivity,
    EarningsData,
    PeerComparison,
    SECFiling,
    AIConsensus,
    InvestmentScore,
    FinancialHealth,
    AeonScore,
    ScenarioAnalysis,
    RevenueBreakdown,
    MomentumData,
    ValueGrowthProfile,
    CompetitiveMoat,
    RiskRewardProfile,
    DividendAnalysis,
    SentimentResult,
    RiskFactor,
    Catalyst,
    AuditResult,
    AnalystConsensus,
    PriceTarget,
    InstitutionalOwnership,
    ExtendedTechnicals,
    ValuationModels,
    SWOTAnalysis,
    InvestmentThesis,
    NewsHeadline,
} from '../../shared/types';

import type { AnalysisResponse } from '../../shared/types';
import { ANALYTICS_URL } from './config';

/** Cache TTL: 4 hours in milliseconds */
const CACHE_TTL_MS = 4 * 60 * 60 * 1000;

// ─── App State ─────────────────────────────────────────────────────
type AppView = 'setup' | 'analysis' | 'report';

interface AppState {
    view: AppView;
    setView: (v: AppView) => void;
    /** Which top-level tab is active — lives here (not component state) so
     * the nav bar can switch tabs (e.g. "Manage Keys" always jumps to
     * Research) without prop-drilling through the whole tree. */
    activeTab: string;
    setActiveTab: (t: string) => void;
    keys: APIKeys | null;
    demoMode: boolean;
    setKeys: (k: APIKeys | null) => void;
    setDemoMode: (d: boolean) => void;
    /** The one global ticker — drives the nav search, every live engine tab
     * (Markets, Agents, Fusion, Houston, Deep Reports/Research, Compare) and
     * the Research report form. Persisted so it survives a reload. */
    ticker: string;
    recent: string[];
    isAnalyzing: boolean;
    analysisPhase: string;
    result: AnalysisResponse | null;
    error: string | null;
    /** Currently in-flight ticker — prevents duplicate concurrent requests */
    _inflightTicker: string | null;
    setTicker: (t: string) => void;
    runAnalysis: (workerUrl?: string) => Promise<void>;
    clearResult: () => void;
}

const DEFAULT_WORKER_URL = import.meta.env.VITE_WORKER_URL || 'http://localhost:8787';

export const useStore = create<AppState>((set, get) => ({
    view: 'setup',
    setView: (v) => set({ view: v }),
    activeTab: 'overview',
    setActiveTab: (t) => set({ activeTab: t }),
    keys: null,
    demoMode: false,
    setKeys: (k) => set({ keys: k }),
    setDemoMode: (d) => set({ demoMode: d }),
    ticker: localStorage.getItem('aeonnimbus_global_ticker') || 'AAPL',
    recent: JSON.parse(localStorage.getItem('aeonnimbus_recent_tickers') || '[]'),
    isAnalyzing: false,
    analysisPhase: '',
    result: null,
    error: null,
    _inflightTicker: null,
    setTicker: (t) => {
        const up = t.toUpperCase().trim();
        if (!up || !/^[A-Z0-9.-]{1,10}$/.test(up)) return;
        const { ticker: prev, recent: prevRecent } = get();
        const recent = [prev, ...prevRecent.filter((r) => r !== up && r !== prev)].filter(Boolean).slice(0, 5);
        localStorage.setItem('aeonnimbus_global_ticker', up);
        localStorage.setItem('aeonnimbus_recent_tickers', JSON.stringify(recent));
        set({ ticker: up, recent });
    },
    clearResult: () => set({ result: null, error: null }),

    runAnalysis: async (workerUrl?: string) => {
        const { ticker: rawTicker, keys, demoMode, _inflightTicker } = get();
        if (!rawTicker) return;
        const ticker = rawTicker.toUpperCase().trim();

        // Prevent duplicate concurrent requests for the same ticker
        if (_inflightTicker === ticker) return;
        set({ _inflightTicker: ticker });

        // Migrate legacy af_ keys on first use
        migrateLegacyKeys();

        // --- CACHE CHECK (encrypted) ---
        if (!demoMode) {
            try {
                const cached = localStorage.getItem(`aeonnimbus_cache_${ticker}`);
                if (cached) {
                    const decrypted = await decryptCache(cached);
                    if (decrypted) {
                        const parsedData = JSON.parse(decrypted) as AnalysisResponse;
                        const cacheTime = new Date(parsedData.timestamp).getTime();
                        if (Date.now() - cacheTime < CACHE_TTL_MS) {
                            set({ result: parsedData, view: 'report', error: null, analysisPhase: '', _inflightTicker: null });
                            return; // Use cache
                        }
                    }
                }
            } catch {
                // Ignore cache read errors
            }
        }

        set({ isAnalyzing: true, error: null, result: null, analysisPhase: '⚡ Collecting financial data, sentiment & risks...' });

        try {
            const url = workerUrl || DEFAULT_WORKER_URL;
            const requestKeys = demoMode
                ? { finnhub: '', groq: '', gemini: '', cohere: '', cerebras: '' }
                : keys || { finnhub: '', groq: '', gemini: '', cohere: '' };

            // Security: Send API keys in encrypted header, not in request body
            const res = await fetch(`${url}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-AeonNimbus-Keys': btoa(JSON.stringify(requestKeys)),
                },
                body: JSON.stringify({ ticker }),
            });

            if (!res.ok) {
                const err = (await res.json().catch(() => ({ error: 'Request failed' }))) as { error?: string };
                throw new Error(err.error || `HTTP ${res.status}`);
            }

            set({ analysisPhase: '📊 Processing results...' });
            const data = (await res.json()) as AnalysisResponse;

            // --- SAVE TO CACHE (encrypted) ---
            if (!demoMode) {
                try {
                    const encrypted = await encryptCache(JSON.stringify(data));
                    localStorage.setItem(`aeonnimbus_cache_${ticker}`, encrypted);
                } catch {
                    // Cache is best-effort
                }
            }

            set({ result: data, view: 'report', analysisPhase: '' });

            // Best-effort save to History & Replay; demo results are mock data, so skip them
            if (!demoMode)
                fetch(`${ANALYTICS_URL}/api/analyses/save`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ticker, result: data, user_id: 1 }),
                }).catch(() => {});
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Analysis failed';
            set({ error: msg, analysisPhase: '' });
        } finally {
            set({ _inflightTicker: null, isAnalyzing: false });
        }
    },
}));
