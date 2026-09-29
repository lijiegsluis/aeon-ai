const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Event dates are stored as naive local-exchange times ("2026-10-02T08:30:00").
 * Parse the parts by hand so the browser's timezone never shifts the day. */
export function formatEventDate(iso: string | null | undefined): string {
    if (!iso) return '—';
    const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/.exec(iso);
    if (!m) return iso;
    const [, y, mo, d, hh, mm] = m;
    const date = new Date(Number(y), Number(mo) - 1, Number(d));
    const day = `${DAYS[date.getDay()]}, ${MONTHS[date.getMonth()]} ${date.getDate()}`;
    const withYear = date.getFullYear() !== new Date().getFullYear() ? `${day}, ${y}` : day;
    if (!hh || (hh === '00' && mm === '00')) return withYear;
    const h = Number(hh);
    return `${withYear} · ${h % 12 || 12}:${mm} ${h < 12 ? 'AM' : 'PM'}`;
}

export function formatMoney(n: number | null | undefined): string {
    if (n == null) return '—';
    const a = Math.abs(n);
    if (a >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (a >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
    if (a >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
}

/** Relative time for news rows: "12m ago", "3h ago", then a short date. */
export function timeAgo(iso: string | null | undefined): string {
    if (!iso) return '—';
    const t = new Date(iso).getTime();
    if (Number.isNaN(t)) return iso;
    const mins = Math.round((Date.now() - t) / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    if (mins < 60 * 24) return `${Math.round(mins / 60)}h ago`;
    return new Date(t).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
