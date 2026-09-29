/**
 * Tiny markdown renderer for briefs: headings, bullet lists, **bold**, _italic_,
 * `code` and paragraphs. Builds React elements (no innerHTML), so brief text can
 * never inject markup.
 */
import { Fragment, type ReactNode } from 'react';

function inline(text: string): ReactNode[] {
    const out: ReactNode[] = [];
    const re = /(\*\*[^*]+\*\*|`[^`]+`|(?<![\w])_[^_]+_(?![\w]))/g;
    let last = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(text))) {
        if (m.index > last) out.push(text.slice(last, m.index));
        const t = m[0];
        if (t.startsWith('**')) out.push(<strong key={m.index}>{t.slice(2, -2)}</strong>);
        else if (t.startsWith('`')) out.push(<code key={m.index}>{t.slice(1, -1)}</code>);
        else out.push(<em key={m.index}>{t.slice(1, -1)}</em>);
        last = m.index + t.length;
    }
    if (last < text.length) out.push(text.slice(last));
    return out;
}

export default function MiniMarkdown({ text }: { text: string }) {
    const blocks: ReactNode[] = [];
    let list: string[] = [];
    const flush = () => {
        if (list.length) {
            blocks.push(
                <ul key={`ul${blocks.length}`} className="mb-3 list-disc space-y-1 pl-5 text-sm text-white/80">
                    {list.map((li, i) => (
                        <li key={i}>{inline(li)}</li>
                    ))}
                </ul>,
            );
            list = [];
        }
    };
    text.split('\n').forEach((raw, i) => {
        const line = raw.trimEnd();
        const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
        if (bullet) {
            list.push(bullet[1]);
            return;
        }
        flush();
        const h = /^(#{1,3})\s+(.*)$/.exec(line);
        if (h) {
            const cls =
                h[1].length === 1
                    ? 'mb-2 text-lg font-bold text-gold'
                    : 'mb-1 mt-3 text-xs font-semibold uppercase tracking-wider text-white/50';
            blocks.push(
                <p key={i} className={cls}>
                    {inline(h[2])}
                </p>,
            );
        } else if (line.trim()) {
            blocks.push(
                <p key={i} className="mb-2 text-sm text-white/70">
                    {inline(line)}
                </p>,
            );
        }
    });
    flush();
    return <Fragment>{blocks}</Fragment>;
}
