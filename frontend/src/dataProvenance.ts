/**
 * Canonical registry of what powers Aeon Analysis, and whether each source
 * is live/real data or an in-house approximation. Single source of truth
 * for two consumers that used to disagree independently:
 *   - Terminal.tsx's SourceBadge (per-tab "is this real?" indicator)
 *   - About.tsx's open-source attribution table
 * Add an engine here once; both surfaces pick up the change.
 */
export interface DataSource {
    id: string;
    /** Badge label shown in-context (product-branded, e.g. "Aeon Markets"). */
    label: string;
    /** Generic engine name shown in the About/licensing table. Defaults to `label`. */
    engineName?: string;
    /** One-line description of what it does. */
    role: string;
    /** true = live external data or a genuinely independent engine; false = Aeon-native approximation/mock. */
    real: boolean;
    /** Open-source license, only set for engines credited in the About screen. */
    license?: string;
}

export const DATA_SOURCES: DataSource[] = [
    { id: 'market-data', label: 'Aeon Markets', engineName: 'Market data layer', role: 'Live quotes, fundamentals, history', real: true, license: 'AGPL-3.0' },
    { id: 'multi-agent', label: 'Multi-Agent Engine', engineName: 'Multi-agent debate', role: 'Analyst → researcher → trader → risk debate', real: true, license: 'Apache-2.0' },
    { id: 'deep-report', label: 'Deep Report Engine', role: 'Institutional equity research reports', real: true, license: 'Apache-2.0' },
    { id: 'deep-research', label: 'Deep Research Agents', role: 'Hierarchical RAG over filings', real: true, license: 'MIT' },
    { id: 'terminal-core', label: 'Desktop Terminal Core', role: 'Native workstation companion', real: true, license: 'AGPL-3.0' },
    { id: 'quant-native', label: 'Aeon native', role: 'In-house quant models — Monte Carlo, CAPM-based DCF, Fusion valuation ensemble', real: false },
    { id: 'personas-native', label: 'Aeon native', role: 'Persona commentary grounded in each persona\'s own computed metric', real: false },
];

export function getSource(id: string): DataSource | undefined {
    return DATA_SOURCES.find((s) => s.id === id);
}
