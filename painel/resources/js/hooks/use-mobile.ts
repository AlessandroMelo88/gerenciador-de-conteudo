import * as React from 'react';

const MOBILE_BREAKPOINT = 768;
const MOBILE_MEDIA_QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`;

function subscribe(onStoreChange: () => void) {
    if (typeof window === 'undefined') {
        return () => undefined;
    }

    const mediaQuery = window.matchMedia(MOBILE_MEDIA_QUERY);
    mediaQuery.addEventListener('change', onStoreChange);
    return () => mediaQuery.removeEventListener('change', onStoreChange);
}

function getSnapshot() {
    return typeof window !== 'undefined' && window.matchMedia(MOBILE_MEDIA_QUERY).matches;
}

function getServerSnapshot() {
    return false;
}

export function useIsMobile() {
    return React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
