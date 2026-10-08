/**
 * useRouteMeta.js — Tiny hook that fires setRouteMeta whenever the screen
 * or its relevant params change.
 *
 * Usage:
 *   useRouteMeta('TitleDetail', { item });
 *
 * The hook intentionally does not render anything; it's a side-effect-only
 * hook that runs in any screen that calls it.
 */
import { useEffect, useRef } from 'react';
import { setRouteMeta } from './seo';

export function useRouteMeta(screen, params) {
    const paramsRef = useRef(params || {});
    paramsRef.current = params || {};

    useEffect(() => {
        // Snapshot at mount / screen change to avoid stale-closure surprises.
        setRouteMeta(screen, paramsRef.current);
    }, [screen]);
}
