import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
    View, Text, StyleSheet, TouchableOpacity,
    SafeAreaView, ActivityIndicator, Platform, useWindowDimensions
} from 'react-native';
import { COLORS } from '../theme/colors';
import Poster from '../components/Poster';
import ShadowStreamPlayer from '../components/ShadowStreamPlayer';
import { getApiBase } from '../utils/api';
import { resolveMirrors, toPlayerProps } from '../utils/resolver';
import { WatchlistAPI } from '../utils/storage';
import { useRouteMeta } from '../utils/useRouteMeta';

export default function PlayerScreen({ route, navigation }) {
    const { item: rawItem, slug: routeSlug, season: routeSeason, episode: routeEpisode } = route.params || {};
    const initialItem = (rawItem && typeof rawItem === 'object') ? rawItem : null;
    const [item, setItem] = useState(initialItem);
    const slug = routeSlug || initialItem?.slug || (initialItem?.id ? String(initialItem.id) : null);

    const isTv = (item?.type || initialItem?.type) === 'tv' ||
        (item?.type || initialItem?.type) === 'short_drama' ||
        ((item?.type || initialItem?.type) === 'anime' && (
            (item?.seasonCount != null && item.seasonCount > 0) ||
            (initialItem?.seasonCount != null && initialItem.seasonCount > 0) ||
            (Array.isArray(item?.seasons) && item.seasons.length > 0)
        ));
    // On web the deep link is the only thing carrying season/episode on a cold
    // load — the router does not map a bare query string into `route.params`,
    // so `/play/slug?season=5&episode=7` used to silently boot S1E1. Read the
    // URL directly and let the route param win when both are present.
    const webQuery = useMemo(() => {
        if (typeof window === 'undefined' || !window.location) return {};
        try {
            return new URLSearchParams(window.location.search || '');
        } catch (e) {
            return {};
        }
    }, []);

    const initialSeason = routeSeason != null ? routeSeason : (webQuery.get ? webQuery.get('season') : null);
    const initialEpisode = routeEpisode != null ? routeEpisode : (webQuery.get ? webQuery.get('episode') : null);

    const parsedSeason = parseInt(initialSeason, 10);
    const parsedEpisode = parseInt(initialEpisode, 10);

    // Explicit season/episode wins over everything. It used to be gated behind
    // `isTv`, but on a cold deep link there is no `item` yet, so `isTv` is
    // false at init and the season collapsed to null — the fetch then set it to
    // 1 and the requested episode was lost. So: use the explicit value if we
    // have one, otherwise fall back to the item/TV default.
    const [currentSeason, setCurrentSeason] = useState(
        Number.isFinite(parsedSeason) ? parsedSeason : (isTv ? (item?.season || 1) : null)
    );
    const [currentEpisode, setCurrentEpisode] = useState(
        Number.isFinite(parsedEpisode) ? parsedEpisode : (isTv ? (item?.episode || 1) : null)
    );

    // Keep the address bar honest so a reload or a shared link lands on the
    // episode actually being watched.
    useEffect(() => {
        if (typeof window === 'undefined' || !window.history?.replaceState) return;
        if (!isTv || currentSeason == null || currentEpisode == null) return;
        const url = new URL(window.location.href);
        if (url.searchParams.get('season') === String(currentSeason)
            && url.searchParams.get('episode') === String(currentEpisode)) return;
        url.searchParams.set('season', String(currentSeason));
        url.searchParams.set('episode', String(currentEpisode));
        window.history.replaceState({}, '', url.toString());
    }, [isTv, currentSeason, currentEpisode]);
    const [seasons, setSeasons] = useState(item?.seasons || []);
    const [dubs, setDubs] = useState(
        initialItem?.audioLanguages ||
        initialItem?.audio_languages ||
        initialItem?.spoken_languages ||
        initialItem?.languages ||
        []
    );

    // NOTE: the global popup guard lives in src/utils/adShield.js, installed
    // once by App.js. This screen used to install a second, stricter override
    // that swallowed the app's own navigation — that conflict is gone.

    // Resolve title data if navigated directly or refreshed via URL
    useEffect(() => {
        if (item || !slug) return;
        let cancelled = false;
        async function fetchTitleData() {
            try {
                const res = await fetch(`${getApiBase()}/title/${encodeURIComponent(slug)}`);
                if (res.ok && !cancelled) {
                    const data = await res.json();
                    setItem(data);
                    const titleIsTv = data.type === 'tv' ||
                        data.type === 'short_drama' ||
                        (data.type === 'anime' && ((data.seasonCount != null && data.seasonCount > 0) || (Array.isArray(data.seasons) && data.seasons.length > 0)));
                    if (titleIsTv) {
                        if (!currentSeason) setCurrentSeason(1);
                        if (!currentEpisode) setCurrentEpisode(1);
                    }
                    if (Array.isArray(data.seasons) && data.seasons.length > 0) {
                        setSeasons(data.seasons);
                    }
                    const detectedDubs = data.audioLanguages || data.audio_languages || data.spoken_languages || data.languages;
                    if (Array.isArray(detectedDubs) && detectedDubs.length > 0) {
                        setDubs(detectedDubs);
                    }
                } else if (!cancelled) {
                    setLoadError(
                        res.status === 404
                            ? `We couldn't find "${slug}" in the catalogue.`
                            : `The catalogue is not responding (HTTP ${res.status}).`
                    );
                }
            } catch (e) {
                if (!cancelled) {
                    setLoadError(`Couldn't reach the catalogue: ${e.message}`);
                }
                console.warn('[PlayerScreen] fetchTitleData error:', e.message);
            }
        }
        fetchTitleData();
        return () => { cancelled = true; };
    // Season/episode used to be deps here, so every episode click refetched the
    // whole title payload and re-set `seasons`, re-rendering the drawer
    // mid-selection. Title metadata does not depend on the play position.
    }, [item?.id, item?.slug, slug]);

    useRouteMeta('Player', {
        title: isTv && currentSeason
            ? `${item?.title || 'Watch'} (S${currentSeason}:E${currentEpisode})`
            : (item?.title || 'Watch')
    });

    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState(null);
    const [streamUrl, setStreamUrl] = useState(item?.streamUrl || item?.playbackUrl || null);
    const [streamKind, setStreamKind] = useState(null); // 'direct' | 'embed' | 'metadata'
    const [sourceName, setSourceName] = useState(null);
    const [mirrorList, setMirrorList] = useState([]); // [{label, provider, url, quality, direct, resolveMode}]
    const [activeMirrorIdx, setActiveMirrorIdx] = useState(0);
    const [resolveNote, setResolveNote] = useState(null);
    const [renditions, setRenditions] = useState([]);

    // Apply a mirror to the player. `direct` wins when the resolver produced
    // one, so our own engine decodes; otherwise the provider iframe plays.
    const applyMirror = useCallback((mirror, idx = 0) => {
        if (!mirror) return;
        const props = toPlayerProps(mirror);
        setStreamUrl(props.streamUrl);
        setStreamKind(props.streamKind);
        setSourceName(props.sourceName);
        setActiveMirrorIdx(idx);
    }, []);

    // Fetch seasons/episodes structure for TV series, and dubs for all titles
    useEffect(() => {
        if (!item) return;
        let cancelled = false;
        async function fetchSeasons() {
            try {
                const res = await fetch(`${getApiBase()}/title/${encodeURIComponent(item.id || item.slug)}/seasons`);
                if (res.ok && !cancelled) {
                    const data = await res.json();
                    if (Array.isArray(data.seasons) && data.seasons.length > 0) {
                        setSeasons(data.seasons);
                    }
                }
            } catch (e) {
                console.warn('[PlayerScreen] fetchSeasons error:', e.message);
            }
        }
        async function fetchDubs() {
            try {
                const res = await fetch(`${getApiBase()}/title/${encodeURIComponent(item.id || item.slug)}/audio-languages`);
                if (res.ok && !cancelled) {
                    const data = await res.json();
                    if (Array.isArray(data.languages) && data.languages.length > 0) {
                        setDubs(data.languages);
                    }
                }
            } catch (e) {
                console.warn('[PlayerScreen] fetchDubs error:', e.message);
            }
        }
        if (isTv) fetchSeasons();
        fetchDubs();
        return () => { cancelled = true; };
    }, [item?.id, item?.slug, isTv]);

    // Resolve playback stream and mirrors, then ask the worker which of them we
    // can actually decode ourselves.
    const resolveStream = useCallback(async () => {
        if (!item) {
            // Previously this returned early without ever clearing `loading`,
            // so a title that failed to load left the player spinning on
            // "Initializing ShadowStream Player..." forever. Now we surface a
            // real error the user can act on.
            setLoading(false);
            setStreamKind('metadata');
            return;
        }
        setLoading(true);

        // Check if stream was passed directly in route params
        if (item.streamUrl || item.playbackUrl) {
            setStreamUrl(item.streamUrl || item.playbackUrl);
            setStreamKind('direct');
            setSourceName(item.sourceName || 'Direct Stream');
            setLoading(false);
            return;
        }

        try {
            const queryParams = new URLSearchParams();
            if (currentSeason) queryParams.set('season', String(currentSeason));
            if (currentEpisode) queryParams.set('episode', String(currentEpisode));

            const res = await fetch(`${getApiBase()}/title/${encodeURIComponent(item.id || item.slug)}/availability?${queryParams.toString()}`);
            let avList = [];
            if (res.ok) {
                const data = await res.json();
                avList = data.availability || [];
            }

            const playableSources = avList.filter(a =>
                (a.kind === 'playback' || a.kind === 'embed') && (a.playbackUrl || a.url || a.external_url)
            );

            if (playableSources.length > 0) {
                // The catalogue offers every scraper it happens to have on file —
                // Dexter hands back four, and a long tail of half-dead embedders
                // on older titles. Showing all of them made the server list
                // noise rather than a choice, so we keep a short, ordered list:
                // one entry per provider (a provider offering five qualities is
                // still one player to the user), ranked, and capped.
                //
                // Ranking, most-trusted first:
                //   vidlink      vidlink.pro, TMDB-ID based
                //   vidsrc       vidsrc.to,  TMDB-ID based
                //   vidsrc_imdb  vidsrc.me,  IMDb-ID based — a different site on
                //                a different ID system, not a duplicate of
                //                vidsrc, and worth keeping as a fallback
                //   2embed       demoted. Loaded fine but its inner player
                //                returned "No content available for this title"
                //                for Dexter S5E7, so it only earns a slot when a
                //                title has nothing better.
                const PROVIDER_RANK = ['vidlink', 'vidsrc', 'vidsrc_imdb', '2embed', 'vid_src'];
                const MAX_MIRRORS = 3;

                const byProvider = new Map();
                for (const a of playableSources) {
                    const key = String(a.source || a.sourceName || 'unknown').toLowerCase();
                    if (!byProvider.has(key)) byProvider.set(key, a);
                }
                const ranked = Array.from(byProvider.values()).sort((a, b) => {
                    const ra = PROVIDER_RANK.indexOf(String(a.source || '').toLowerCase());
                    const rb = PROVIDER_RANK.indexOf(String(b.source || '').toLowerCase());
                    return (ra === -1 ? 99 : ra) - (rb === -1 ? 99 : rb);
                });
                const kept = ranked.slice(0, MAX_MIRRORS);

                const mirrors = kept.map(a => ({
                    label: a.sourceName || a.source || 'Mirror',
                    provider: a.source || 'embed',
                    url: a.kind === 'playback' ? (a.playbackUrl || a.url) : (a.url || a.external_url || a.playbackUrl),
                    format: a.kind === 'playback' ? 'video' : 'embed',
                    quality: 'HD'
                }));

                // Give every mirror a chance to become a direct stream. This is
                // best-effort and bounded; a failure leaves the mirror usable
                // as an iframe, which is the whole point of the fallback.
                const { playable, mirrors: resolved, anyDirect } = await resolveMirrors(mirrors, {
                    tmdbId: item.tmdbId || item.tmdb_id,
                    type: item.type,
                    season: currentSeason,
                    episode: currentEpisode,
                });

                setMirrorList(resolved);
                setResolveNote(
                    anyDirect
                        ? null
                        : 'Playing via the provider’s own player — no direct stream was available to decode.'
                );
                const idx = Math.max(0, resolved.indexOf(playable));
                applyMirror(playable, idx);
                setLoading(false);
                return;
            }

            // Fallback to metadata-only discovery state
            setStreamKind('metadata');
        } catch (e) {
            console.warn('[PlayerScreen] resolveStream error:', e.message);
            setStreamKind('metadata');
        } finally {
            setLoading(false);
        }
        // Alternate encodes for the quality menu. Progressive files have no
        // HLS levels, so without this the menu is empty on almost every title.
        if (item) {
            try {
                const key = item.id || item.slug;
                const r = await fetch(`${getApiBase()}/title/${encodeURIComponent(key)}/renditions`);
                if (r.ok) {
                    const d = await r.json();
                    const list = [];
                    for (const src of d.renditions || []) {
                        for (const o of src.options || []) list.push(o);
                    }
                    setRenditions(list);
                }
            } catch (_) { /* quality options are optional */ }
        }
    }, [applyMirror, item, currentSeason, currentEpisode]);

    useEffect(() => {
        resolveStream();
    }, [resolveStream]);

    // Handle user selecting an episode from the in-player drawer
    const handleSelectEpisode = useCallback((seasonNum, episodeNum) => {
        const s = parseInt(seasonNum, 10);
        const e = parseInt(episodeNum, 10);
        // Episode rows from the catalogue carry no season of their own. This
        // used to be called with `undefined` and set the season to null, which
        // drops `season` from the availability query and pins the player to
        // S1E1 forever. Ignore anything non-numeric instead.
        if (!Number.isFinite(s) || !Number.isFinite(e)) {
            console.warn('[PlayerScreen] ignored episode selection', { seasonNum, episodeNum });
            return;
        }
        if (s === currentSeason && e === currentEpisode) return;
        setCurrentSeason(s);
        setCurrentEpisode(e);
    }, [currentSeason, currentEpisode]);

    // Handle auto-advancing or clicking "Next Episode"
    const handleNextEpisode = useCallback(() => {
        const curSeasonObj = seasons.find(s => s.season_number === (currentSeason || 1)) || seasons[0];
        const epList = curSeasonObj?.episodes || [];
        const curIdx = epList.findIndex(e => e.episode_number === currentEpisode);

        if (curIdx !== -1 && curIdx < epList.length - 1) {
            // Next episode in current season
            const nextEp = epList[curIdx + 1];
            setCurrentEpisode(nextEp.episode_number);
        } else {
            // Check next season
            const curSeasonIdx = seasons.findIndex(s => s.season_number === (currentSeason || 1));
            if (curSeasonIdx !== -1 && curSeasonIdx < seasons.length - 1) {
                const nextSeason = seasons[curSeasonIdx + 1];
                setCurrentSeason(nextSeason.season_number);
                setCurrentEpisode(nextSeason.episodes?.[0]?.episode_number || 1);
            }
        }
    }, [seasons, currentSeason, currentEpisode]);

    if (loading) {
        return (
            <SafeAreaView style={styles.screen}>
                <View style={styles.centerContainer}>
                    <ActivityIndicator size="large" color={COLORS.brand} />
                    <Text style={styles.loadingText}>
                        {loadError ? 'Something went wrong' : 'Initializing ShadowStream Player...'}
                    </Text>
                    <Text style={styles.loadingSub}>
                        {loadError || (isTv && currentSeason
                            ? `Connecting to ${item?.title} (S${currentSeason}:E${currentEpisode})...`
                            : 'Connecting to high-speed stream server...')}
                    </Text>
                    {loadError ? (
                        <TouchableOpacity
                            style={styles.retryBtn}
                            onPress={() => { setLoadError(null); setLoading(true); resolveStream(); }}
                        >
                            <Text style={styles.retryBtnText}>Try again</Text>
                        </TouchableOpacity>
                    ) : null}
                </View>
            </SafeAreaView>
        );
    }

    // Main Player: Full Screen, Edge-to-Edge
    if (streamUrl && (streamKind === 'direct' || streamKind === 'embed')) {
        return (
            <SafeAreaView style={styles.screen}>
                <ShadowStreamPlayer
                    title={item?.title}
                    season={currentSeason}
                    episode={currentEpisode}
                    streamUrl={streamUrl}
                    streamKind={streamKind}
                    sourceName={sourceName}
                    seasons={seasons}
                    mirrorList={mirrorList}
                    activeMirrorIdx={activeMirrorIdx}
                    dubs={dubs}
                    onSelectMirror={applyMirror}
                    onSelectEpisode={handleSelectEpisode}
                    onNextEpisode={handleNextEpisode}
                    onBack={() => navigation.goBack()}
                    mediaId={item?.id || item?.slug}
                    renditions={renditions}
                    notice={resolveNote}
                />
            </SafeAreaView>
        );
    }

    // Metadata / Discovery State (Only shown if no playable stream is found)
    return (
        <SafeAreaView style={styles.screen}>
            <View style={styles.metadataStateContainer}>
                <Poster
                    url={item?.backdrop || item?.poster}
                    title={item?.title}
                    style={StyleSheet.absoluteFill}
                />
                <View style={styles.metadataStateOverlay}>
                    <TouchableOpacity style={styles.backBtnFloating} onPress={() => navigation.goBack()}>
                        <Text style={styles.backBtnText}>‹ Back</Text>
                    </TouchableOpacity>

                    <View style={styles.metadataBadge}>
                        <Text style={styles.metadataBadgeText}>SHADOWSTREAM</Text>
                    </View>
                    <Text style={styles.metadataTitle}>{item?.title}</Text>
                    <Text style={styles.metadataNotice}>
                        No active stream source was found for this title. You can search online or check IMDb.
                    </Text>
                    <View style={styles.officialLinksRow}>
                        <TouchableOpacity
                            style={styles.officialLinkBtn}
                            onPress={() => window?.open?.(`https://www.google.com/search?q=${encodeURIComponent((item?.title || '') + ' watch online')}`, '_blank')}
                        >
                            <Text style={styles.officialLinkText}>🌐 Web Search</Text>
                        </TouchableOpacity>
                        {item?.imdbId && (
                            <TouchableOpacity
                                style={styles.officialLinkBtn}
                                onPress={() => window?.open?.(`https://www.imdb.com/title/${item.imdbId}/`, '_blank')}
                            >
                                <Text style={styles.officialLinkText}>⭐ IMDb</Text>
                            </TouchableOpacity>
                        )}
                    </View>
                </View>
            </View>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    screen: {
        flex: 1,
        backgroundColor: '#000000',
        width: '100%',
        height: '100%',
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20,
    },
    loadingText: { color: COLORS.textPrimary, fontSize: 15, fontWeight: '700', marginTop: 16 },
    loadingSub: { color: COLORS.textMuted, fontSize: 12, marginTop: 4 },
    retryBtn: {
        marginTop: 20,
        backgroundColor: COLORS.brand,
        borderRadius: 6,
        paddingHorizontal: 22,
        paddingVertical: 11,
    },
    retryBtnText: { color: '#FFFFFF', fontSize: 15, fontWeight: '700' },
    metadataStateContainer: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: COLORS.surface,
    },
    metadataStateOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(10, 10, 10, 0.92)',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 30,
    },
    backBtnFloating: {
        position: 'absolute',
        top: 20,
        left: 20,
        paddingHorizontal: 14,
        paddingVertical: 8,
        backgroundColor: 'rgba(20, 20, 20, 0.8)',
        borderRadius: 6,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.15)',
    },
    backBtnText: { color: '#FFFFFF', fontSize: 14, fontWeight: '700' },
    metadataBadge: {
        backgroundColor: 'rgba(229, 9, 20, 0.15)',
        borderWidth: 1,
        borderColor: 'rgba(229, 9, 20, 0.4)',
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 4,
        marginBottom: 14,
    },
    metadataBadgeText: { color: COLORS.brand, fontSize: 10, fontWeight: '800', letterSpacing: 0.8 },
    metadataTitle: {
        color: COLORS.textPrimary,
        fontSize: 26,
        fontWeight: '900',
        textAlign: 'center',
        marginBottom: 12,
    },
    metadataNotice: {
        color: COLORS.textSecondary,
        fontSize: 13,
        textAlign: 'center',
        maxWidth: 500,
        lineHeight: 20,
        marginBottom: 20,
    },
    officialLinksRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: 12,
    },
    officialLinkBtn: {
        backgroundColor: COLORS.surfaceAlt,
        paddingHorizontal: 16,
        paddingVertical: 10,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: COLORS.border,
    },
    officialLinkText: {
        color: COLORS.textPrimary,
        fontSize: 13,
        fontWeight: '700',
    },
});
