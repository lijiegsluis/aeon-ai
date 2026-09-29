export type Product = {
    icon: string;
    layer: string;
    name: string;
    tag: string;
    desc: string;
    status: 'live' | 'wip' | 'desktop';
    href: string | null;
    video: string;
};

export const PRODUCTS: Product[] = [
    {
        icon: '📊',
        layer: 'Foundation Layer',
        name: 'Aeon Analysis',
        tag: 'Know WHAT to buy',
        desc: 'A 14-tab local research terminal — a 5-method valuation ensemble (DCF, Graham, Lynch, analyst targets, Monte Carlo), an AI council with real multi-agent debate, and 55-field reports with bull/base/bear scenarios.',
        status: 'live',
        href: 'http://localhost:5173',
        video: '/videos/tool-analysis.mp4',
    },
    {
        icon: '⚡',
        layer: 'Event Layer',
        name: 'Aeon Intelligence',
        tag: 'Know WHEN to trade',
        desc: 'A D-X countdown timeline for earnings and macro releases, sorted into 4 timing phases, with a 90-day insider-trade tracker and categorized AI-prediction views.',
        status: 'live',
        href: 'http://localhost:5175',
        video: '/videos/tool-intelligence.mp4',
    },
    {
        icon: '🎯',
        layer: 'Research Layer',
        name: 'Aeon Platform',
        tag: 'From filings to published call',
        desc: 'Turns company filings into institutional research — a sourced Data Studio pipeline, a Bull/Base/Bear DCF model, a published buy/sell/hold call with price target and stop-loss, and Aeon Score factor rankings across your coverage universe.',
        status: 'live',
        href: 'http://localhost:5174',
        video: '/videos/tool-platform.mp4',
    },
    {
        icon: '💻',
        layer: 'Execution Layer',
        name: 'Aeon Terminal',
        tag: "Know what's happening NOW",
        desc: 'A local financial workstation that fuses five open-source finance engines plus original Aeon analytics into one instrument — live watchlists, multi-agent research, and quant tools running natively on your machine, not in a browser tab. Open source: clone it and run one script to start every service.',
        status: 'desktop',
        href: 'PLACEHOLDER_GITHUB_REPO_URL',
        video: '/videos/tool-terminal.mp4',
    },
];

export const JOURNEY = [
    {
        n: '01',
        title: 'Research',
        product: 'Aeon Analysis',
        desc: 'Run any ticker through the 5-method valuation ensemble and AI council to find mispriced names.',
        out: '"AAPL undervalued 12%. Strong fundamentals. BUY candidate."',
    },
    {
        n: '02',
        title: 'Time it',
        product: 'Aeon Intelligence',
        desc: 'Check the D-X countdown for the name — earnings, CPI, FOMC — and the current phase.',
        out: '"Enter now (D-12, Accumulation). Exit D-1."',
    },
    {
        n: '03',
        title: 'Synthesize',
        product: 'Aeon Platform',
        desc: 'Turn the thesis into a full research report — Bull/Base/Bear DCF, a published call, ranked by Aeon Score.',
        out: '"AAPL: BUY, PT $210, entry $185, stop $170. Aeon Score: 82."',
    },
    {
        n: '04',
        title: 'Monitor',
        product: 'Aeon Terminal',
        desc: 'Keep the ticker on your watchlist — live price tape, sentiment score, and the next event countdown.',
        out: '"AAPL sentiment +0.42 this week. Next event: earnings in 6 days."',
    },
];
