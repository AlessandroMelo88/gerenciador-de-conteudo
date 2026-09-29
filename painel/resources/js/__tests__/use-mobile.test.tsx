import { renderHook } from '@testing-library/react';

import { useIsMobile } from '@/hooks/use-mobile';

function mockMatchMedia(matches: boolean) {
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
    }));
}

describe('useIsMobile', () => {
    it('true em viewport estreito', () => {
        mockMatchMedia(true);
        expect(renderHook(() => useIsMobile()).result.current).toBe(true);
    });

    it('false em desktop', () => {
        mockMatchMedia(false);
        expect(renderHook(() => useIsMobile()).result.current).toBe(false);
    });
});
