/**
 * Global command palette (⌘K / Ctrl+K) — jump to any tab, open the vault,
 * launch the desktop app, or set the ticker, all from one place. The
 * single strongest signal that this is one instrument, not ten separate
 * pages: every surface is reachable the same way, instantly.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useStore } from '../store';

type Cmd = { id: string; icon: string; label: string; hint?: string; run: () => void };

export default function CommandPalette({ tabs }: { tabs: { id: string; label: string }[] }) {
    const [open, setOpen] = useState(false);
    const [q, setQ] = useState('');
    const [sel, setSel] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const setActiveTab = useStore((s) => s.setActiveTab);
    const setView = useStore((s) => s.setView);
    const { ticker, setTicker } = useStore();

    const commands = useMemo<Cmd[]>(() => {
        const jump: Cmd[] = tabs.map((t) => ({
            id: `tab:${t.id}`,
            icon: '→',
            label: `Go to ${t.label.replace(/^\S+\s/, '')}`,
            hint: 'tab',
            run: () => setActiveTab(t.id),
        }));
        const actions: Cmd[] = [
            {
                id: 'vault',
                icon: '🔑',
                label: 'Open Key Vault',
                hint: 'settings',
                run: () => {
                    setActiveTab('research');
                    setView('setup');
                },
            },
            { id: 'about', icon: '✦', label: 'About & Licenses', hint: 'info', run: () => setActiveTab('about') },
        ];
        if (q && /^[A-Za-z0-9.-]{1,10}$/.test(q.trim())) {
            actions.unshift({
                id: 'ticker',
                icon: '🎯',
                label: `Set ticker to ${q.trim().toUpperCase()}`,
                hint: 'enter',
                run: () => setTicker(q.trim()),
            });
        }
        return [...actions, ...jump];
    }, [tabs, q, setActiveTab, setView, setTicker]);

    const filtered = useMemo(() => {
        const query = q.trim().toLowerCase();
        if (!query) return commands;
        return commands.filter((c) => c.label.toLowerCase().includes(query));
    }, [commands, q]);

    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                setOpen((o) => !o);
            } else if (e.key === 'Escape' && open) {
                setOpen(false);
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [open]);

    useEffect(() => {
        if (open) {
            setQ('');
            setSel(0);
            setTimeout(() => inputRef.current?.focus(), 10);
        }
    }, [open]);

    useEffect(() => setSel(0), [q]);

    const runSelected = (i: number) => {
        const c = filtered[i];
        if (!c) return;
        c.run();
        setOpen(false);
    };

    if (!open) return null;

    return (
        <div
            className="fixed inset-0 z-[100] flex items-start justify-center pt-[12vh]"
            style={{ background: 'rgba(6,11,20,0.75)', backdropFilter: 'blur(4px)' }}
            onClick={() => setOpen(false)}
        >
            <div className="card-premium w-full max-w-lg animate-scale-in overflow-hidden p-0" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
                    <span className="text-accent">⌘</span>
                    <input
                        ref={inputRef}
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'ArrowDown') {
                                e.preventDefault();
                                setSel((s) => Math.min(s + 1, filtered.length - 1));
                            } else if (e.key === 'ArrowUp') {
                                e.preventDefault();
                                setSel((s) => Math.max(s - 1, 0));
                            } else if (e.key === 'Enter') {
                                e.preventDefault();
                                runSelected(sel);
                            }
                        }}
                        placeholder={`Jump anywhere, set a ticker, or run an action… (current: ${ticker})`}
                        className="w-full bg-transparent text-sm text-white placeholder-white/30 outline-none"
                    />
                    <kbd className="rounded border border-white/10 px-1.5 py-0.5 text-[10px] text-white/30">esc</kbd>
                </div>
                <div className="max-h-[50vh] overflow-y-auto py-2">
                    {filtered.length === 0 && <p className="px-4 py-6 text-center text-sm text-white/30">No matches</p>}
                    {filtered.map((c, i) => (
                        <button
                            key={c.id}
                            onClick={() => runSelected(i)}
                            onMouseEnter={() => setSel(i)}
                            className={`flex w-full items-center justify-between px-4 py-2 text-left text-sm transition-colors ${
                                i === sel ? 'bg-accent/10 text-white' : 'text-white/70'
                            }`}
                        >
                            <span className="flex items-center gap-2.5">
                                <span className="w-4 text-center">{c.icon}</span>
                                {c.label}
                            </span>
                            {c.hint && <span className="text-[10px] uppercase tracking-wider text-white/25">{c.hint}</span>}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
