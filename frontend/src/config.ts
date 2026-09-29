/** Every service URL the terminal talks to, overridable per deploy via Vite env vars.
 * Defaults are the local ports start-terminal.sh (and intelligence/start.sh) use. */
const env = import.meta.env;

/** Aeon analytics API (quotes, quant, fusion, Houston, events, persistence). */
export const ANALYTICS_URL: string = env.VITE_ANALYTICS_URL || 'http://127.0.0.1:8000';
/** Research report worker (55-dimension report). */
export const WORKER_URL: string = env.VITE_WORKER_URL || 'http://localhost:8787';
/** Sister apps the terminal links into. */
export const INTELLIGENCE_APP_URL: string = env.VITE_INTELLIGENCE_URL || 'http://localhost:5175';
export const PLATFORM_APP_URL: string = env.VITE_PLATFORM_URL || 'http://localhost:5174';

/** Optional open-source engines, run locally by start-terminal.sh. */
export const OPENBB_URL: string = env.VITE_OPENBB_URL || 'http://127.0.0.1:6900';
export const TRADING_AGENTS_URL: string = env.VITE_TRADING_AGENTS_URL || 'http://127.0.0.1:8001';
export const FINROBOT_URL: string = env.VITE_FINROBOT_URL || 'http://127.0.0.1:8002';
export const DEEP_RESEARCH_URL: string = env.VITE_DEEP_RESEARCH_URL || 'http://127.0.0.1:8600';

/** Link to a ticker's lens in Aeon Intelligence. */
export const intelligenceTickerUrl = (ticker: string) => `${INTELLIGENCE_APP_URL}/?ticker=${encodeURIComponent(ticker)}`;
