/** Shared JSON fetch helpers for the Aeon-backed engine tabs (Terminal, Fusion, Houston). */

/** FastAPI returns `detail` as a string, or as a list of validation errors (422). */
export function errorDetail(body: unknown, fallback: string): string {
    const detail = (body as { detail?: unknown } | null)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail.map((d: { msg?: string; loc?: unknown[] }) => (d?.msg ?? String(d)).replace(/^Value error, /, '')).join('; ');
    }
    return fallback;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
    let r: Response;
    try {
        r = await fetch(url, init);
    } catch {
        // fetch only rejects when the request never got an HTTP answer
        throw new Error(`Service unreachable (${new URL(url).host}) — is it running?`);
    }
    if (!r.ok) throw new Error(errorDetail(await r.json().catch(() => null), r.statusText || `HTTP ${r.status}`));
    return r.json();
}

export function jget<T>(url: string): Promise<T> {
    return request<T>(url);
}

export function jpost<T>(url: string, body: unknown): Promise<T> {
    return request<T>(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
}

export function jdelete<T>(url: string): Promise<T> {
    return request<T>(url, { method: 'DELETE' });
}
