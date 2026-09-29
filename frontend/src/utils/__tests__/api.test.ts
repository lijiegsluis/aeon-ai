import { afterEach, describe, expect, it, vi } from 'vitest';
import { errorDetail, jget } from '../api';
import { humanizeErr } from '../../components/Terminal';

describe('errorDetail', () => {
    it('reads FastAPI string details', () => {
        expect(errorDetail({ detail: 'no data for ticker' }, 'x')).toBe('no data for ticker');
    });
    it('joins 422 validation errors instead of printing [object Object]', () => {
        const body = { detail: [{ msg: 'Value error, invalid ticker: $$$' }, { msg: 'field required' }] };
        expect(errorDetail(body, 'x')).toBe('invalid ticker: $$$; field required');
    });
    it('falls back when the body has no detail', () => {
        expect(errorDetail(null, 'Bad Gateway')).toBe('Bad Gateway');
    });
});

describe('jget', () => {
    afterEach(() => vi.unstubAllGlobals());
    it('names the unreachable host when fetch rejects', async () => {
        vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
        await expect(jget('http://127.0.0.1:8000/health')).rejects.toThrow('Service unreachable (127.0.0.1:8000)');
    });
    it('surfaces the backend detail on HTTP errors', async () => {
        vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'nope' }), { status: 404 })));
        await expect(jget('http://x.test/a')).rejects.toThrow('nope');
    });
});

describe('humanizeErr', () => {
    it('does not mistake an invalid ticker for a rejected API key', () => {
        expect(humanizeErr('Error: invalid ticker')).toBe('invalid ticker');
    });
    it('explains rejected keys and unreachable services', () => {
        expect(humanizeErr('400 Client Error: API key not valid')).toMatch(/API key was rejected/);
        expect(humanizeErr('TypeError: Failed to fetch')).toMatch(/Service unreachable/);
    });
});
