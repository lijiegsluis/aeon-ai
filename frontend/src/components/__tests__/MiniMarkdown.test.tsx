import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import MiniMarkdown from '../MiniMarkdown';

describe('MiniMarkdown', () => {
    it('renders headings, lists and inline emphasis', () => {
        const html = renderToStaticMarkup(<MiniMarkdown text={'# Brief\n\n## Next\n- **D-1** · CPI\n- plain `x`\n\n_note_'} />);
        expect(html).toContain('>Brief</p>');
        expect(html).toContain('<li><strong>D-1</strong> · CPI</li>');
        expect(html).toContain('<code>x</code>');
        expect(html).toContain('<em>note</em>');
    });
    it('never injects markup from the text', () => {
        const html = renderToStaticMarkup(<MiniMarkdown text={'<img src=x onerror=alert(1)>'} />);
        expect(html).not.toContain('<img');
        expect(html).toContain('&lt;img');
    });
});
