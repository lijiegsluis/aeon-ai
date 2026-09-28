/** Shared JSON fetch helpers for the Aeon-backed engine tabs (Terminal, Fusion, Houston). */

export async function jget<T>(url: string): Promise<T> {
    const r = await fetch(url);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
    return r.json();
}

export async function jpost<T>(url: string, body: unknown): Promise<T> {
    const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
    return r.json();
}
