import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity,
    SafeAreaView, ActivityIndicator, Alert, useWindowDimensions, Modal, Pressable, Linking
} from 'react-native';
import { COLORS } from '../theme/colors';
import AppHeader from '../components/AppHeader';
import MobileTabBar from '../components/MobileTabBar';
import Poster from '../components/Poster';
import MediaCard from '../components/MediaCard';
import { getApiBase } from '../utils/api';
import { WatchlistAPI, HistoryAPI } from '../utils/storage';
import { useRouteMeta } from '../utils/useRouteMeta';

const LANGUAGE_NAMES = {
    en: 'English',
    ja: 'Japanese',
    hi: 'Hindi',
    ur: 'Urdu',
    es: 'Spanish',
    fr: 'French',
    de: 'German',
    ko: 'Korean',
    zh: 'Chinese',
    ar: 'Arabic',
    it: 'Italian',
    pt: 'Portuguese',
    ru: 'Russian',
    tr: 'Turkish',
    ta: 'Tamil',
    te: 'Telugu',
    bn: 'Bengali',
    id: 'Indonesian',
    tl: 'Tagalog',
    th: 'Thai',
    vi: 'Vietnamese',
    fa: 'Persian',
    pa: 'Punjabi',
};

function formatLanguage(l) {
    if (!l) return '';
    if (typeof l === 'string') {
        const code = l.toLowerCase().trim();
        return LANGUAGE_NAMES[code] || l.toUpperCase();
    }
    const code = String(l.code || l.iso || l.language || '').toLowerCase().trim();
    return l.label || l.name || LANGUAGE_NAMES[code] || (code ? code.toUpperCase() : '');
}

export default function TitleDetailScreen({ route, navigation }) {
    // Support both navigation patterns:
    //   - in-app:    route.params.item is a populated MediaItem-like object
    //   - deep link: route.params.slug (or route.params.id) is the only source
    //                — we resolve by slug via GET /api/v1/title/{slug}
    const params = route.params || {};
    const initialItem = params.item;
    const slugFromUrl = params.slug || params.id || null;

    const { width } = useWindowDimensions();
    const isDesktop = width >= 768;

    const titleKey = initialItem?.id || initialItem?.slug || slugFromUrl;
    const [item, setItem] = useState(initialItem || null);
    const [seasons, setSeasons] = useState([]);
    const [activeSeasonNum, setActiveSeasonNum] = useState(1);
    const [cast, setCast] = useState([]);
    const [similar, setSimilar] = useState([]);
    const [franchise, setFranchise] = useState(null);
    const [inWatchlist, setInWatchlist] = useState(false);
    const [loadingDetail, setLoadingDetail] = useState(true);
    const [loadError, setLoadError] = useState(null);
    const [trailerUrl, setTrailerUrl] = useState(null);

    // Inject the YouTube iframe imperatively after mount (RN Web View doesn't render <iframe> children).
    const trailerHostRef = useRef(null);
    useEffect(() => {
        if (trailerHostRef.current && typeof document !== 'undefined') {
            if (trailerUrl) {
                const safeUrl = trailerUrl.replace(/"/g, '&quot;');
                const safeTitle = (item?.title || 'Trailer').replace(/"/g, '&quot;');
                trailerHostRef.current.innerHTML =
                    `<iframe src="${safeUrl}" style="position:absolute;inset:0;width:100%;height:100%;border:0;display:block;background:#000" allow="autoplay; encrypted-media; accelerometer; gyroscope; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin" title="${safeTitle} — YouTube embed"></iframe>`;
            } else {
                trailerHostRef.current.innerHTML = '';
            }
        }
    }, [trailerUrl, item?.title]);

    useRouteMeta('TitleDetail', item);

    const isEpisodic = (item?.type || initialItem?.type) === 'tv' ||
        (item?.type || initialItem?.type) === 'short_drama' ||
        ((item?.type || initialItem?.type) === 'anime' && (
            (item?.seasonCount != null && item.seasonCount > 0) ||
            (initialItem?.seasonCount != null && initialItem.seasonCount > 0) ||
            (Array.isArray(item?.seasons) && item.seasons.length > 0)
        ));

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoadingDetail(true);
            setLoadError(null);
            try {
                // 1. Fetch full title detail (works for both ID and slug)
                const detailRes = await fetch(`${getApiBase()}/title/${encodeURIComponent(titleKey)}`);
                if (!detailRes.ok) {
                    if (!cancelled) {
                        setLoadError(detailRes.status === 404 ? 'not_found' : `http_${detailRes.status}`);
                    }
                    return;
                }
                const detailData = await detailRes.json();
                if (!cancelled) {
                    setItem(prev => ({ ...(prev || {}), ...detailData }));

                    // 4. Fetch similar titles
                    const firstGenre = detailData.genres && detailData.genres[0]
                        ? (detailData.genres[0].slug || detailData.genres[0])
                        : null;
                    if (firstGenre) {
                        fetch(`${getApiBase()}/titles?genre=${encodeURIComponent(firstGenre)}&page_size=8`)
                            .then(r => r.json())
                            .then(simData => {
                                if (!cancelled) setSimilar((simData.items || []).filter(t => t.id !== detailData.id));
                            })
                            .catch(() => {});
                    }
                }

                // 2. If episodic, fetch seasons and episodes
                if (isEpisodic) {
                    const seasonsRes = await fetch(`${getApiBase()}/title/${encodeURIComponent(titleKey)}/seasons`);
                    if (seasonsRes.ok) {
                        const sData = await seasonsRes.json();
                        if (!cancelled) {
                            const sList = sData.seasons || [];
                            setSeasons(sList);
                            if (sList.length > 0) {
                                setActiveSeasonNum(sList[0].season_number || 1);
                            }
                        }
                    }
                }

                // 3. Fetch cast
                const castRes = await fetch(`${getApiBase()}/title/${encodeURIComponent(titleKey)}/cast`);
                if (castRes.ok) {
                    const castData = await castRes.json();
                    if (!cancelled) {
                        setCast(castData.cast || []);
                    }
                }

                // 4. Fetch franchise / collection (movies only)
                if (detailData.type === 'movie') {
                    fetch(`${getApiBase()}/title/${encodeURIComponent(titleKey)}/franchise`)
                        .then(r => r.ok ? r.json() : null)
                        .then(frData => {
                            if (!cancelled && frData && frData.collection) {
                                setFranchise(frData);
                            }
                        })
                        .catch(() => { /* swallow */ });
                }
            } catch (err) {
                console.error('[TitleDetailScreen] load error:', err);
            } finally {
                if (!cancelled) setLoadingDetail(false);
            }
        }

        load();
        setInWatchlist(WatchlistAPI.isSaved(titleKey));
        return () => { cancelled = true; };
    }, [titleKey, isEpisodic]);

    const toggleWatchlist = () => {
        if (inWatchlist) {
            WatchlistAPI.remove(item.id);
            setInWatchlist(false);
            Alert.alert('Removed', `${item.title} removed from Watchlist`);
        } else {
            WatchlistAPI.add(item);
            setInWatchlist(true);
            Alert.alert('Saved', `${item.title} added to Watchlist`);
        }
    };

    // If we don't have an item yet (loading or failed), show a loader.
    // Catches: cold start from deep link, post-route-change, fetch failure, etc.
    if (!item) {
        return (
            <SafeAreaView style={styles.screen}>
                <AppHeader navigation={navigation} title={titleKey ? 'Loading…' : 'Title'} />
                <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 }}>
                    {loadError === 'not_found' ? (
                        <>
                            <Text style={{ color: COLORS.textPrimary, fontSize: 22, fontWeight: '700', marginBottom: 8 }}>Title not found</Text>
                            <Text style={{ color: COLORS.textMuted, fontSize: 14, textAlign: 'center' }}>
                                We couldn't find "{titleKey}". It may have been removed or the link is incorrect.
                            </Text>
                            <TouchableOpacity onPress={() => navigation.navigate('Home')} style={{ marginTop: 20, paddingHorizontal: 18, paddingVertical: 10, backgroundColor: COLORS.brand, borderRadius: 6 }}>
                                <Text style={{ color: '#fff', fontWeight: '700' }}>Back to Home</Text>
                            </TouchableOpacity>
                        </>
                    ) : loadError ? (
                        <>
                            <Text style={{ color: COLORS.textPrimary, fontSize: 22, fontWeight: '700', marginBottom: 8 }}>Couldn't load title</Text>
                            <Text style={{ color: COLORS.textMuted, fontSize: 14, textAlign: 'center' }}>Server returned {loadError}. Try again in a moment.</Text>
                        </>
                    ) : (
                        <>
                            <ActivityIndicator size="large" color={COLORS.brand} />
                            <Text style={{ color: COLORS.textMuted, fontSize: 14, marginTop: 16 }}>Looking up "{titleKey}"…</Text>
                        </>
                    )}
                </View>
            </SafeAreaView>
        );
    }

    const safeItem = item;
    const availList = Array.isArray(item.availability) ? item.availability : [];
    const directPlayback = availList.find(a => a.kind === 'playback' && (a.playbackUrl || a.playback_url));
    const embedPlayback = availList.find(a => a.kind === 'embed' && (a.url || a.external_url));
    const isPlayable = Boolean(directPlayback || embedPlayback || item.has_playback || item.tmdbId || item.imdbId || item.id);
    const downloadable = availList.find(a => a.isDownloadable && (a.playbackUrl || a.playback_url));
    const watchProviders = Array.isArray(item.watchProviders) ? item.watchProviders : [];
    const activeSeason = seasons.find(s => s.season_number === activeSeasonNum) || seasons[0] || null;
    const episodes = activeSeason?.episodes || [];

    const playTitleOrEpisode = (ep) => {
        if (!item) return;
        const payload = {
            slug: item.slug || String(item.id),
            item,
            season: isEpisodic ? (ep ? (ep.season_number || activeSeasonNum) : (activeSeasonNum || 1)) : null,
            episode: isEpisodic ? (ep ? ep.episode_number : 1) : null,
        };
        navigation.navigate('Player', payload);
    };

    const openTrailerModal = (url) => {
        if (!url) return;
        // Convert YouTube watch URLs to embed URLs
        let embedUrl = url;
        const m = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]{6,})/);
        if (m && m[1]) {
            embedUrl = `https://www.youtube.com/embed/${m[1]}?autoplay=1&modestbranding=1&rel=0`;
        }
        setTrailerUrl(embedUrl);
    };
    const closeTrailerModal = () => setTrailerUrl(null);

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} title={item.title} />

            <ScrollView showsVerticalScrollIndicator={false}>
                {/* Hero Backdrop Banner */}
                <View style={[styles.heroBanner, isDesktop && styles.heroBannerDesktop]}>
                    <Poster
                        url={item.backdrop || item.poster}
                        title={item.title}
                        style={StyleSheet.absoluteFill}
                        resizeMode="cover"
                    />
                    <View style={styles.heroOverlay} />

                    <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
                        <Text style={styles.backBtnText}>‹ Back</Text>
                    </TouchableOpacity>

                    <View style={styles.heroContentRow}>
                        <View style={styles.posterContainer}>
                            <Poster
                                url={item.poster}
                                title={item.title}
                                style={StyleSheet.absoluteFill}
                            />
                        </View>

                        <View style={styles.heroInfoCol}>
                            <View style={styles.typeBadgeRow}>
                                <View style={styles.typeBadge}>
                                    <Text style={styles.typeBadgeText}>
                                        {(item.type || 'movie').toUpperCase().replace('_', ' ')}
                                    </Text>
                                </View>
                                {item.rating ? (
                                    <View style={styles.ratingBadge}>
                                        <Text style={styles.ratingStar}>★</Text>
                                        <Text style={styles.ratingText}>{Number(item.rating).toFixed(1)}</Text>
                                    </View>
                                ) : null}
                            </View>

                            <Text style={styles.mainTitle}>{item.title}</Text>

                            {item.originalTitle && item.originalTitle !== item.title && (
                                <Text style={styles.origTitle}>{item.originalTitle}</Text>
                            )}

                            <View style={styles.metaChipsRow}>
                                {item.year && <Text style={styles.metaChip}>{item.year}</Text>}
                                {item.runtime && <Text style={styles.metaChip}>{item.runtime}m</Text>}
                                {item.seasons && <Text style={styles.metaChip}>{item.seasons} Seasons</Text>}
                                {isPlayable && <Text style={[styles.metaChip, styles.metaChipGreen]}>Verified Stream</Text>}
                            </View>

                            {/* CTAs */}
                            <View style={styles.actionButtonsRow}>
                                <TouchableOpacity
                                    style={[styles.playBtn, !isPlayable && {opacity: 0.5}]}
                                    onPress={() => isPlayable ? playTitleOrEpisode(null) : null}
                                    activeOpacity={0.8}
                                    accessibilityRole="button"
                                    accessibilityLabel={`Play ${item.title}`}
                                >
                                    <Text style={styles.playBtnIcon}>▶</Text>
                                    <Text style={styles.playBtnText}>Watch Now</Text>
                                </TouchableOpacity>

                                <TouchableOpacity
                                    style={[styles.watchlistBtn, inWatchlist && styles.watchlistBtnActive]}
                                    onPress={toggleWatchlist}
                                    activeOpacity={0.8}
                                >
                                    <Text style={styles.watchlistIcon}>{inWatchlist ? '✓' : '+'}</Text>
                                    <Text style={styles.watchlistText}>{inWatchlist ? 'In Watchlist' : 'Watchlist'}</Text>
                                </TouchableOpacity>

                                {downloadable ? (
                                    <TouchableOpacity
                                        style={styles.trailerBtn}
                                        onPress={() => Linking.openURL(downloadable.playbackUrl || downloadable.playback_url)}
                                        activeOpacity={0.8}
                                        accessibilityRole="button"
                                        accessibilityLabel={`Download ${item.title}`}
                                    >
                                        <Text style={styles.trailerBtnIcon}>⬇</Text>
                                        <Text style={styles.trailerBtnText}>Download</Text>
                                    </TouchableOpacity>
                                ) : null}

                                {item.trailerUrl ? (
                                    <TouchableOpacity
                                        style={styles.trailerBtn}
                                        onPress={() => openTrailerModal(item.trailerUrl)}
                                        activeOpacity={0.8}
                                        accessibilityRole="button"
                                        accessibilityLabel={`Watch trailer for ${item.title}`}
                                    >
                                        <Text style={styles.trailerBtnIcon}>🎬</Text>
                                        <Text style={styles.trailerBtnText}>Trailer</Text>
                                    </TouchableOpacity>
                                ) : null}
                            </View>
                        </View>
                    </View>
                </View>

                {/* Stream Availability Status Banner */}
                <View style={styles.statusBannerWrapper}>
                    {isPlayable ? (
                        <View style={styles.availBannerSuccess}>
                            <Text style={styles.availBannerIcon}>✅</Text>
                            <View style={{ flex: 1 }}>
                                <Text style={styles.availBannerTitle}>Stream Ready</Text>
                                <Text style={styles.availBannerSub}>
                                    Tap "Watch Now" - the Player streams directly from {directPlayback?.sourceName || 'available verified sources'}.
                                </Text>
                            </View>
                        </View>
                    ) : watchProviders.length > 0 ? (
                        <View style={styles.availBannerInfo}>
                            <Text style={styles.availBannerIcon}>📡</Text>
                            <View style={{ flex: 1 }}>
                                <Text style={styles.availBannerTitle}>Available Elsewhere</Text>
                                <Text style={styles.availBannerSub}>
                                    Not in our lawful catalog yet, but already streaming on a real licensed service.
                                </Text>
                                <View style={styles.langPillsRow}>
                                    {watchProviders.map((p, idx) => (
                                        <TouchableOpacity
                                            key={`${p.slug}-${p.type}-${idx}`}
                                            style={styles.metaChip}
                                            onPress={() => p.deepLink && Linking.openURL(p.deepLink)}
                                        >
                                            <Text style={{ color: COLORS.text }}>
                                                {p.name}{p.type === 'subscription' ? '' : ` (${p.type})`}
                                            </Text>
                                        </TouchableOpacity>
                                    ))}
                                </View>
                            </View>
                        </View>
                    ) : (
                        <View style={styles.availBannerInfo}>
                            <Text style={styles.availBannerIcon}>ℹ</Text>
                            <View style={{ flex: 1 }}>
                                <Text style={styles.availBannerTitle}>Metadata Only</Text>
                                <Text style={styles.availBannerSub}>
                                    This title is currently not available for streaming. Check back later.
                                </Text>
                            </View>
                        </View>
                    )}
                </View>

                {/* Synopsis & Tagline */}
                <View style={styles.sectionBlock}>
                    <Text style={styles.sectionHeaderTitle}>STORYLINE</Text>
                    {item.tagline && <Text style={styles.tagline}>"{item.tagline}"</Text>}
                    <Text style={styles.overviewText}>
                        {item.overview || item.description || 'Full synopsis currently being cataloged.'}
                    </Text>
                </View>

                {/* Languages — dubs + subs availability */}
                {(item.audioLanguages?.length > 0 || item.subtitleLanguages?.length > 0 || item.languages?.length > 0) && (
                    <View style={styles.sectionBlock}>
                        <Text style={styles.sectionHeaderTitle}>🗣️ LANGUAGES & DUBBING</Text>
                        <View style={styles.langPillsRow}>
                            {item.audioLanguages && item.audioLanguages.length > 0 && (
                                <View style={styles.langGroup}>
                                    <Text style={styles.langGroupHeader}>🎙️ Audio Dubs</Text>
                                    <View style={styles.langPillsRow}>
                                        {item.audioLanguages.map((l, idx) => {
                                            const label = formatLanguage(l);
                                            if (!label) return null;
                                            return (
                                                <View key={`audio-${idx}`} style={[styles.langPill, styles.langPillAudio]}>
                                                    <Text style={styles.langPillText}>{label}</Text>
                                                </View>
                                            );
                                        })}
                                    </View>
                                </View>
                            )}
                            {item.subtitleLanguages && item.subtitleLanguages.length > 0 && (
                                <View style={styles.langGroup}>
                                    <Text style={styles.langGroupHeader}>📝 Subtitles</Text>
                                    <View style={styles.langPillsRow}>
                                        {item.subtitleLanguages.map((l, idx) => {
                                            const label = formatLanguage(l);
                                            if (!label) return null;
                                            return (
                                                <View key={`sub-${idx}`} style={[styles.langPill, styles.langPillSub]}>
                                                    <Text style={styles.langPillText}>{label}</Text>
                                                </View>
                                            );
                                        })}
                                    </View>
                                </View>
                            )}
                            {item.languages && item.languages.length > 0 && (
                                <View style={styles.langGroup}>
                                    <Text style={styles.langGroupHeader}>🌐 Original</Text>
                                    <View style={styles.langPillsRow}>
                                        {item.languages.map((l, idx) => {
                                            const label = formatLanguage(l);
                                            if (!label) return null;
                                            return (
                                                <View key={`lang-${idx}`} style={[styles.langPill, styles.langPillOrig]}>
                                                    <Text style={styles.langPillText}>{label}</Text>
                                                </View>
                                            );
                                        })}
                                    </View>
                                </View>
                            )}
                        </View>
                    </View>
                )}

                {/* Cast & Countries */}
                {(item.countries && item.countries.length > 0) && (
                    <View style={styles.sectionBlock}>
                        <Text style={styles.sectionHeaderTitle}>🌍 ORIGIN</Text>
                        <View style={styles.langPillsRow}>
                            {item.countries.map((c, idx) => (
                                <View key={`country-${c.code || idx}`} style={[styles.langPill, styles.langPillCountry]}>
                                    <Text style={styles.langPillText}>{c.flag || '🌐'} {c.name || c.code}</Text>
                                </View>
                            ))}
                        </View>
                    </View>
                )}

                {/* Episodic Season & Episode Selector */}
                {isEpisodic && (
                    <View style={styles.sectionBlock}>
                        <View style={styles.seasonHeaderRow}>
                            <Text style={styles.sectionHeaderTitle}>EPISODES</Text>
                            {seasons.length > 1 && (
                                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.seasonsChipsRow}>
                                    {seasons.map(s => {
                                        const isSel = activeSeasonNum === s.season_number;
                                        return (
                                            <TouchableOpacity
                                                key={s.id || s.season_number}
                                                style={[styles.seasonChip, isSel && styles.seasonChipActive]}
                                                onPress={() => setActiveSeasonNum(s.season_number)}
                                            >
                                                <Text style={[styles.seasonChipText, isSel && styles.seasonChipTextActive]}>
                                                    Season {s.season_number}
                                                </Text>
                                            </TouchableOpacity>
                                        );
                                    })}
                                </ScrollView>
                            )}
                        </View>

                        {/* Episodes List */}
                        <View style={styles.episodesList}>
                            {episodes.map(ep => (
                                <TouchableOpacity
                                    key={ep.id || ep.episode_number}
                                    style={styles.episodeCard}
                                    onPress={() => playTitleOrEpisode(ep)}
                                    activeOpacity={0.8}
                                >
                                    <View style={styles.epThumbWrapper}>
                                        <Poster
                                            url={ep.thumbnail || item.backdrop || item.poster}
                                            title={`Ep ${ep.episode_number}`}
                                            style={StyleSheet.absoluteFill}
                                        />
                                        <View style={styles.epPlayOverlay}>
                                            <Text style={styles.epPlayOverlayIcon}>▶</Text>
                                        </View>
                                    </View>

                                    <View style={styles.epInfo}>
                                        <View style={styles.epTitleRow}>
                                            <Text style={styles.epNumText}>E{ep.episode_number}</Text>
                                            <Text style={styles.epTitleText} numberOfLines={1}>{ep.title}</Text>
                                        </View>
                                        <Text style={styles.epOverview} numberOfLines={2}>
                                            {ep.overview || 'Episode synopsis available in database.'}
                                        </Text>
                                        {ep.runtime && <Text style={styles.epRuntimeText}>{ep.runtime} min</Text>}
                                    </View>
                                </TouchableOpacity>
                            ))}
                        </View>
                    </View>
                )}

                {/* Franchise / Collection (movies only — Baahubali 1+2, Star Wars saga, etc.) */}
                {franchise && franchise.parts && franchise.parts.length > 1 && (
                    <View style={styles.sectionBlock}>
                        <View style={{ marginBottom: 12 }}>
                            <Text style={styles.sectionHeaderTitle}>🎬 FRANCHISE — {franchise.collection.name}</Text>
                            <Text style={{ color: COLORS.textMuted, fontSize: 12, marginTop: 4 }}>
                                {franchise.parts.length} films in this saga
                            </Text>
                        </View>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 14, paddingHorizontal: 4 }}>
                            {franchise.parts.map((part) => (
                                <TouchableOpacity
                                    key={part.id}
                                    style={[styles.franchiseCard, part.is_current && styles.franchiseCardCurrent]}
                                    onPress={() => {
                                        if (part.is_current) return;
                                        navigation.navigate('TitleDetail', { slug: part.slug || String(part.id), item: part });
                                    }}
                                    activeOpacity={part.is_current ? 1 : 0.85}
                                    accessibilityLabel={`${part.title}, ${part.year || ''}`}
                                    accessibilityRole="button"
                                >
                                    <View style={styles.franchiseThumb}>
                                        <Poster url={part.poster} title={part.title} style={StyleSheet.absoluteFill} />
                                        {part.is_current && (
                                            <View style={styles.franchiseYouBadge}>
                                                <Text style={styles.franchiseYouBadgeText}>YOU ARE HERE</Text>
                                            </View>
                                        )}
                                    </View>
                                    <Text style={styles.franchiseTitle} numberOfLines={2}>{part.title}</Text>
                                    {part.year && <Text style={styles.franchiseYear}>{part.year}</Text>}
                                </TouchableOpacity>
                            ))}
                        </ScrollView>
                    </View>
                )}

                {/* Cast Carousel */}
                {cast.length > 0 && (
                    <View style={styles.sectionBlock}>
                        <Text style={styles.sectionHeaderTitle}>TOP CAST</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.castRow}>
                            {cast.map((actor, idx) => (
                                <View key={`${actor.id || idx}-${idx}`} style={styles.castCard}>
                                    <View style={styles.castAvatar}>
                                        <Poster
                                            url={actor.profile_image}
                                            title={actor.name}
                                            style={StyleSheet.absoluteFill}
                                        />
                                    </View>
                                    <Text style={styles.actorName} numberOfLines={1}>{actor.name}</Text>
                                    <Text style={styles.characterName} numberOfLines={1}>{actor.character_name || actor.known_for_department}</Text>
                                </View>
                            ))}
                        </ScrollView>
                    </View>
                )}

                {/* Similar Recommendations */}
                {similar.length > 0 && (
                    <View style={styles.sectionBlock}>
                        <Text style={styles.sectionHeaderTitle}>MORE LIKE THIS</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.similarRow}>
                            {similar.map((sim, idx) => (
                                <View key={`${sim.id || idx}-${idx}`} style={{ marginRight: 14 }}>
                                    <MediaCard
                                        item={sim}
                                        onPress={(it) => navigation.push('TitleDetail', { item: it })}
                                    />
                                </View>
                            ))}
                        </ScrollView>
                    </View>
                )}

                <View style={{ height: 40 }} />
            </ScrollView>

            {/* Trailer Modal */}
            <Modal
                visible={!!trailerUrl}
                transparent
                animationType="fade"
                onRequestClose={closeTrailerModal}
                statusBarTranslucent
            >
                <Pressable style={styles.trailerBackdrop} onPress={closeTrailerModal} accessibilityLabel="Close trailer" />
                <View style={styles.trailerContainer} accessibilityViewIsModal>
                    <View style={styles.trailerHeader}>
                        <Text style={styles.trailerHeaderTitle}>🎬 Official Trailer</Text>
                        <Text style={styles.trailerHeaderSub} numberOfLines={1}>{item?.title}</Text>
                        <TouchableOpacity onPress={closeTrailerModal} style={styles.trailerCloseBtn} accessibilityRole="button" accessibilityLabel="Close trailer">
                            <Text style={styles.trailerCloseBtnText}>×</Text>
                        </TouchableOpacity>
                    </View>
                    <View style={styles.trailerFrameWrap}>
                        <View ref={trailerHostRef} style={{ flex: 1, width: '100%', height: '100%' }} />
                    </View>
                </View>
            </Modal>

            <MobileTabBar navigation={navigation} activeRoute="TitleDetail" />
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    screen: { flex: 1, backgroundColor: COLORS.bg },
    heroBanner: {
        height: 400,
        position: 'relative',
        justifyContent: 'flex-end',
        backgroundColor: COLORS.surface
    },
    heroBannerDesktop: {
        height: 480
    },
    heroOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(10, 10, 10, 0.75)'
    },
    backBtn: {
        position: 'absolute',
        top: 16,
        left: 16,
        backgroundColor: 'rgba(0,0,0,0.6)',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 6,
        zIndex: 10
    },
    backBtnText: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },
    heroContentRow: {
        flexDirection: 'row',
        padding: 20,
        alignItems: 'flex-end',
        zIndex: 5
    },
    posterContainer: {
        width: 120,
        height: 180,
        borderRadius: 8,
        overflow: 'hidden',
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.2)',
        backgroundColor: COLORS.surfaceAlt,
        marginRight: 16
    },
    heroInfoCol: {
        flex: 1
    },
    typeBadgeRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginBottom: 6
    },
    typeBadge: {
        backgroundColor: COLORS.brand,
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4
    },
    typeBadgeText: {
        color: '#FFFFFF',
        fontSize: 9,
        fontWeight: '800'
    },
    ratingBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255,255,255,0.15)',
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4
    },
    ratingStar: { color: COLORS.gold, fontSize: 10, marginRight: 3 },
    ratingText: { color: '#FFFFFF', fontSize: 10, fontWeight: '700' },
    mainTitle: {
        color: COLORS.textPrimary,
        fontSize: 24,
        fontWeight: '900',
        letterSpacing: -0.5
    },
    origTitle: {
        color: COLORS.textMuted,
        fontSize: 12,
        marginTop: 2
    },
    metaChipsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        marginTop: 8,
        marginBottom: 14
    },
    metaChip: {
        color: COLORS.textSecondary,
        fontSize: 11,
        fontWeight: '600'
    },
    metaChipGreen: {
        color: COLORS.success,
        fontWeight: '800'
    },
    actionButtonsRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10
    },
    playBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: COLORS.brand,
        paddingHorizontal: 18,
        paddingVertical: 10,
        borderRadius: 6
    },
    playBtnIcon: { color: '#FFFFFF', fontSize: 13, marginRight: 6 },
    playBtnText: { color: '#FFFFFF', fontSize: 13, fontWeight: '700' },
    watchlistBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255,255,255,0.12)',
        paddingHorizontal: 14,
        paddingVertical: 10,
        borderRadius: 6
    },
    watchlistBtnActive: {
        backgroundColor: 'rgba(16, 185, 129, 0.25)'
    },
    watchlistIcon: { color: '#FFFFFF', fontSize: 13, marginRight: 6 },
    watchlistText: { color: '#FFFFFF', fontSize: 12, fontWeight: '600' },
    trailerBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(239, 68, 68, 0.18)',
        borderWidth: 1,
        borderColor: 'rgba(239, 68, 68, 0.55)',
        paddingHorizontal: 14,
        paddingVertical: 9,
        borderRadius: 6
    },
    trailerBtnIcon: { fontSize: 13, marginRight: 6 },
    trailerBtnText: { color: '#FCA5A5', fontSize: 12, fontWeight: '700' },
    trailerBackdrop: {
        position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
        backgroundColor: 'rgba(0,0,0,0.88)',
    },
    trailerContainer: {
        position: 'absolute',
        top: '6%', bottom: '6%', left: '4%', right: '4%',
        backgroundColor: '#0c0d12',
        borderRadius: 14,
        borderWidth: 1, borderColor: 'rgba(239,68,68,0.35)',
        overflow: 'hidden',
        alignSelf: 'center',
        maxWidth: 1080,
    },
    trailerHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: 'rgba(255,255,255,0.06)',
        gap: 12,
    },
    trailerHeaderTitle: { color: '#FCA5A5', fontSize: 13, fontWeight: '700', letterSpacing: 0.5 },
    trailerHeaderSub: { color: '#fff', fontSize: 14, fontWeight: '600', flex: 1 },
    trailerCloseBtn: {
        width: 32, height: 32, borderRadius: 16,
        backgroundColor: 'rgba(255,255,255,0.08)',
        alignItems: 'center', justifyContent: 'center',
    },
    trailerCloseBtnText: { color: '#fff', fontSize: 22, lineHeight: 24, fontWeight: '600' },
    trailerFrameWrap: { flex: 1, backgroundColor: '#000' },
    statusBannerWrapper: {
        paddingHorizontal: 18,
        paddingVertical: 12
    },
    availBannerSuccess: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        borderWidth: 1,
        borderColor: 'rgba(16, 185, 129, 0.3)',
        borderRadius: 8,
        padding: 12
    },
    availBannerInfo: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 1,
        borderColor: 'rgba(59, 130, 246, 0.25)',
        borderRadius: 8,
        padding: 12
    },
    availBannerIcon: { fontSize: 20, marginRight: 12 },
    availBannerTitle: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '700' },
    availBannerSub: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
    sectionBlock: {
        paddingHorizontal: 20,
        paddingVertical: 14
    },
    sectionHeaderTitle: {
        color: COLORS.textMuted,
        fontSize: 11,
        fontWeight: '800',
        letterSpacing: 1,
        marginBottom: 8
    },
    tagline: {
        color: COLORS.textSecondary,
        fontSize: 13,
        fontStyle: 'italic',
        marginBottom: 8
    },
    overviewText: {
        color: COLORS.textSecondary,
        fontSize: 13,
        lineHeight: 20
    },
    langPillsRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 6,
        marginBottom: 12
    },
    langGroup: {
        marginBottom: 8,
        width: '100%'
    },
    langGroupHeader: {
        color: COLORS.textMuted,
        fontSize: 11,
        fontWeight: '700',
        letterSpacing: 0.5,
        marginBottom: 6
    },
    langPill: {
        paddingHorizontal: 9,
        paddingVertical: 4,
        borderRadius: 4,
        borderWidth: 1,
        backgroundColor: 'rgba(255,255,255,0.04)'
    },
    langPillAudio: {
        borderColor: 'rgba(34, 211, 238, 0.5)',
        backgroundColor: 'rgba(34, 211, 238, 0.10)'
    },
    langPillSub: {
        borderColor: 'rgba(167, 139, 250, 0.5)',
        backgroundColor: 'rgba(167, 139, 250, 0.10)'
    },
    langPillOrig: {
        borderColor: COLORS.border,
        backgroundColor: COLORS.surfaceAlt
    },
    langPillCountry: {
        borderColor: 'rgba(255,255,255,0.2)',
        backgroundColor: 'rgba(255,255,255,0.04)'
    },
    langPillText: {
        color: COLORS.textPrimary,
        fontSize: 10,
        fontWeight: '700',
        letterSpacing: 0.3
    },
    seasonHeaderRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12
    },
    seasonsChipsRow: {
        gap: 6
    },
    seasonChip: {
        paddingHorizontal: 12,
        paddingVertical: 5,
        borderRadius: 16,
        backgroundColor: COLORS.surfaceAlt,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    seasonChipActive: {
        backgroundColor: COLORS.badgeTv,
        borderColor: COLORS.badgeTv
    },
    seasonChipText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '600' },
    seasonChipTextActive: { color: '#FFFFFF', fontWeight: '700' },
    episodesList: {
        gap: 10
    },
    episodeCard: {
        flexDirection: 'row',
        backgroundColor: COLORS.surfaceCard,
        borderRadius: 8,
        padding: 10,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    epThumbWrapper: {
        width: 100,
        height: 60,
        borderRadius: 6,
        overflow: 'hidden',
        position: 'relative',
        backgroundColor: COLORS.surfaceAlt
    },
    epPlayOverlay: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: 'rgba(0,0,0,0.3)',
        justifyContent: 'center',
        alignItems: 'center'
    },
    epPlayOverlayIcon: { color: '#FFFFFF', fontSize: 16 },
    epInfo: {
        flex: 1,
        marginLeft: 12,
        justifyContent: 'center'
    },
    epTitleRow: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    epNumText: {
        color: COLORS.brandSecondary,
        fontSize: 12,
        fontWeight: '800',
        marginRight: 6
    },
    epTitleText: {
        color: COLORS.textPrimary,
        fontSize: 13,
        fontWeight: '700',
        flex: 1
    },
    epOverview: {
        color: COLORS.textMuted,
        fontSize: 11,
        marginTop: 2
    },
    epRuntimeText: {
        color: COLORS.textMuted,
        fontSize: 10,
        marginTop: 4
    },
    franchiseCard: {
        width: 140,
        position: 'relative'
    },
    franchiseCardCurrent: {
        opacity: 1
    },
    franchiseThumb: {
        width: 140,
        height: 200,
        borderRadius: 8,
        overflow: 'hidden',
        backgroundColor: COLORS.surface,
        position: 'relative'
    },
    franchiseYouBadge: {
        position: 'absolute',
        bottom: 8,
        left: 8,
        right: 8,
        backgroundColor: COLORS.brand,
        borderRadius: 4,
        paddingVertical: 4,
        paddingHorizontal: 6,
        alignItems: 'center'
    },
    franchiseYouBadgeText: {
        color: '#fff',
        fontSize: 9,
        fontWeight: '800',
        letterSpacing: 1
    },
    franchiseTitle: {
        color: COLORS.textPrimary,
        fontSize: 12,
        fontWeight: '700',
        marginTop: 6,
        maxWidth: 140
    },
    franchiseYear: {
        color: COLORS.textMuted,
        fontSize: 11,
        marginTop: 2
    },
    castRow: {
        paddingTop: 6,
        gap: 14
    },
    castCard: {
        width: 80,
        alignItems: 'center'
    },
    castAvatar: {
        width: 64,
        height: 64,
        borderRadius: 32,
        overflow: 'hidden',
        backgroundColor: COLORS.surfaceAlt,
        marginBottom: 6
    },
    actorName: { color: COLORS.textPrimary, fontSize: 11, fontWeight: '700', textAlign: 'center' },
    characterName: { color: COLORS.textMuted, fontSize: 10, textAlign: 'center' },
    similarRow: {
        paddingTop: 8
    }
});
