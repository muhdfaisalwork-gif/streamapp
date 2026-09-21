import 'react-native-gesture-handler';
import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
    View, Text, StyleSheet, useWindowDimensions, FlatList, Image,
    ActivityIndicator, TouchableOpacity, TextInput, ScrollView,
    SafeAreaView, Platform, Alert, Dimensions
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// Backend API base
const API_BASE = 'http://localhost:3000/api/v1';

const COLORS = {
    bg: '#0a0a0a',
    surface: '#161616',
    surfaceAlt: '#1f1f1f',
    border: '#2a2a2a',
    textPrimary: '#FFFFFF',
    textSecondary: '#A3A3A3',
    textMuted: '#6B7280',
    brand: '#E50914',
    brandSecondary: '#FF1744',
    accent: '#00E5FF',
    success: '#10B981',
    warning: '#F59E0B',
    gradient1: 'rgba(10,10,10,0)',
    gradient2: 'rgba(10,10,10,0.85)',
    gradient3: 'rgba(10,10,10,1)'
};

// =================== STORAGE HELPERS (web-safe localStorage wrapper) ===================
const Storage = {
    get(key, fallback) {
        try {
            if (typeof window !== 'undefined' && window.localStorage) {
                const v = window.localStorage.getItem(key);
                return v ? JSON.parse(v) : fallback;
            }
        } catch (e) { /* ignore */ }
        return fallback;
    },
    set(key, value) {
        try {
            if (typeof window !== 'undefined' && window.localStorage) {
                window.localStorage.setItem(key, JSON.stringify(value));
            }
        } catch (e) { /* ignore */ }
    },
    bump(key, by = 1) {
        try {
            if (typeof window !== 'undefined' && window.localStorage) {
                const cur = Number(window.localStorage.getItem(key) || 0) + by;
                window.localStorage.setItem(key, String(cur));
                return cur;
            }
        } catch (e) { /* ignore */ }
        return 0;
    },
    remove(key) {
        try {
            if (typeof window !== 'undefined' && window.localStorage) {
                window.localStorage.removeItem(key);
            }
        } catch (e) { /* ignore */ }
    }
};

// =================== POSTER (with error fallback) ===================
const DEFAULT_FALLBACK_POSTER = 'https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg';

function Poster({ url, title, style, badge }) {
    const validInitial = url && typeof url === 'string' && url.startsWith('http') && !url.includes('/poster_') ? url : '';
    const [imgSrc, setImgSrc] = useState(validInitial);

    useEffect(() => {
        const u = url && typeof url === 'string' && url.startsWith('http') && !url.includes('/poster_') ? url : '';
        setImgSrc(u);
    }, [url]);

    // Always render the title+emoji fallback below the image. The image element paints
    // on top when it loads successfully; when it fails (cross-origin / network / slow),
    // the fallback remains visible underneath and the card is never a black rectangle.
    return (
        <View style={[style, { width: '100%', overflow: 'hidden', backgroundColor: '#3a3a3a' }]}>
            <View style={[StyleSheet.absoluteFill, { alignItems: 'center', justifyContent: 'center', padding: 6 }]}>
                <Text style={{ fontSize: 28, marginBottom: 6 }}>🎬</Text>
                <Text style={{ color: '#fff', fontSize: 12, fontWeight: '700', textAlign: 'center' }} numberOfLines={2}>
                    {title || 'Loading…'}
                </Text>
            </View>
            {imgSrc ? (
                <Image
                    source={{ uri: imgSrc }}
                    style={[styles.posterImage, StyleSheet.absoluteFill]}
                    resizeMode="cover"
                    fadeDuration={0}
                    progressiveRenderingEnabled={false}
                />
            ) : null}
            {badge && (
                <View style={styles.badge}>
                    <Text style={styles.badgeText}>{badge}</Text>
                </View>
            )}
        </View>
    );
}

// Pick the best available embed quality from a catalog entry (4K > 1080p > 720p)
function getQuality(item) {
    const streams = Array.isArray(item?.streams) ? item.streams : [];
    for (const s of streams) {
        const q = (s?.quality || '').toString();
        if (q.includes('4K') || q.includes('2160')) return { label: '4K', tone: 'gold' };
        if (q.includes('1080')) return { label: 'HD', tone: 'cyan' };
    }
    if (item?.type === 'tv') return { label: 'TV', tone: 'muted' };
    return null;
}

function getSourceLabel(item) {
    const streams = Array.isArray(item?.streams) ? item.streams : [];
    const first = streams[0];
    if (first && first.label) return first.label;
    if (item.sourceName) return item.sourceName;
    if (item.sourceOrigin === 'live') return 'Live';
    return null;
}

function MediaCard({ item, onPress, isLarge, showProgress }) {
    const watchProgress = Storage.get(`progress_${item.id}`, 0);
    const isLive = item.sourceOrigin === 'live' || (item.source && item.source !== 'curated' && item.source !== 'MovieBox');
    const posterUrl = item.poster && typeof item.poster === 'string' && item.poster.startsWith('http') && !item.poster.includes('/poster_') ? item.poster : null;
    return (
        <TouchableOpacity
            style={[styles.card, isLarge && styles.cardLarge, { flexShrink: 0 }]}
            onPress={() => onPress(item)}
            activeOpacity={0.85}
        >
            <View style={styles.cardPoster}>
                {/* Always-rendered visible placeholder so the card is never blank */}
                <View style={[StyleSheet.absoluteFill, { alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.surfaceAlt, padding: 6 }]}>
                    <Text style={{ fontSize: 28, marginBottom: 6 }}>🎬</Text>
                    <Text style={{ color: '#fff', fontSize: 11, fontWeight: '700', textAlign: 'center' }} numberOfLines={2}>
                        {item.title || 'Loading…'}
                    </Text>
                </View>
                {/* Image painted on top when it loads. */}
                {posterUrl ? (
                    <Image
                        source={{ uri: posterUrl }}
                        style={[styles.posterImage, StyleSheet.absoluteFill]}
                        resizeMode="cover"
                        fadeDuration={0}
                    />
                ) : null}
                {item.type === 'tv' ? (
                    <View style={styles.badge}><Text style={styles.badgeText}>TV</Text></View>
                ) : item.rating ? (
                    <View style={styles.badge}><Text style={styles.badgeText}>★ {item.rating}</Text></View>
                ) : null}
            </View>
            <View style={styles.cardInfo}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Text style={{ fontSize: 8, color: isLive ? COLORS.success : COLORS.textMuted, marginRight: 4 }}>●</Text>
                    <Text style={[styles.cardTitle, { flex: 1 }]} numberOfLines={1}>{item.title}</Text>
                </View>
                <Text style={styles.cardMeta}>
                    {item.year || ''} {item.durationMinutes ? `• ${item.durationMinutes}m` : ''} {isLive ? `• ${item.source || 'Live'}` : ''}
                </Text>
            </View>
            {showProgress && watchProgress > 0 && watchProgress < 95 && (
                <View style={styles.progressBarBg}>
                    <View style={[styles.progressBarFill, { width: `${watchProgress}%` }]} />
                </View>
            )}
        </TouchableOpacity>
    );
}

// =================== CATEGORY CAROUSEL ===================
function CategoryRow({ category, onSelectMedia, onSelectCategory }) {
    const items = (category.items || []).slice(0, 30); // cap visible row for perf
    if (items.length === 0) return null;
    return (
        <View style={styles.categorySection}>
            <TouchableOpacity
                style={styles.categoryHeader}
                onPress={() => onSelectCategory && onSelectCategory(category)}
            >
                <Text style={styles.categoryTitle}>{category.title}</Text>
                <Text style={styles.categoryMeta}>{category.count} titles ›</Text>
            </TouchableOpacity>
            {/* Inline horizontal scroll — RN-web can't reliably nest FlatList inside vertical ScrollView */}
            <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.categoryList}
                style={{ width: '100%' }}
            >
                {items.map((item, idx) => (
                    <View key={`${item.id || idx}-${idx}`} style={styles.cardSlot}>
                        <MediaCard
                            item={item}
                            onPress={onSelectMedia}
                            showProgress
                        />
                    </View>
                ))}
                <TouchableOpacity
                    style={[styles.cardSlot, styles.cardSlotMore]}
                    onPress={() => onSelectCategory && onSelectCategory(category)}
                    activeOpacity={0.7}
                >
                    <View style={[styles.cardPoster, styles.cardSlotMorePoster]}>
                        <Text style={styles.cardSlotMoreText}>View All</Text>
                        <Text style={styles.cardSlotMoreCount}>{category.count} ›</Text>
                    </View>
                </TouchableOpacity>
            </ScrollView>
        </View>
    );
}

// =================== LOADING SKELETON ===================
function SkeletonGrid({ count = 6 }) {
    return (
        <View style={styles.skeletonGrid}>
            {Array.from({ length: count }).map((_, i) => (
                <View key={i} style={[styles.skeletonCard, { backgroundColor: COLORS.surfaceAlt }]}>
                    <View style={[styles.skeletonPoster, { backgroundColor: COLORS.border }]} />
                    <View style={[styles.skeletonLine, { backgroundColor: COLORS.border, width: '70%' }]} />
                    <View style={[styles.skeletonLine, { backgroundColor: COLORS.border, width: '40%' }]} />
                </View>
            ))}
        </View>
    );
}

// =================== APP HEADER (Responsive with Hamburger) ===================
function AppHeader({ navigation, title }) {
    const { width } = useWindowDimensions();
    const isLargeScreen = width >= 768;

    const toggleMenu = () => {
        try {
            navigation.toggleDrawer();
        } catch (e) {
            try {
                navigation.getParent('Drawer')?.toggleDrawer();
            } catch (e2) {
                navigation.getParent()?.toggleDrawer();
            }
        }
    };

    return (
        <View style={styles.appHeader}>
            <View style={styles.appHeaderLeft}>
                {!isLargeScreen && (
                    <TouchableOpacity
                        style={styles.hamburgerButton}
                        onPress={toggleMenu}
                        hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                    >
                        <Text style={styles.hamburgerIcon}>☰</Text>
                    </TouchableOpacity>
                )}
                <TouchableOpacity
                    style={styles.appHeaderBrandTouch}
                    onPress={() => navigation.navigate('Home', { screen: 'HomeMain' })}
                >
                    <View style={styles.appHeaderLogo}>
                        <Text style={styles.appHeaderLogoIcon}>🎬</Text>
                    </View>
                    <Text style={styles.appHeaderBrand}>StreamApp</Text>
                </TouchableOpacity>
                {title && (
                    <View style={styles.appHeaderTag}>
                        <Text style={styles.appHeaderTagText}>{title}</Text>
                    </View>
                )}
            </View>
            <View style={styles.appHeaderRight}>
                <TouchableOpacity
                    style={styles.headerIconBtn}
                    onPress={() => navigation.navigate('Search', { screen: 'SearchMain' })}
                >
                    <Text style={styles.headerIconText}>🔍</Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={styles.headerIconBtn}
                    onPress={() => navigation.navigate('Watchlist', { screen: 'WatchlistMain' })}
                >
                    <Text style={styles.headerIconText}>📺</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

// =================== HOME SCREEN ===================
function HomeScreen({ navigation }) {
    const [categories, setCategories] = useState([]);
    const [hero, setHero] = useState(null);
    const [heroSlides, setHeroSlides] = useState([]);
    const [heroIndex, setHeroIndex] = useState(0);
    const [heroPaused, setHeroPaused] = useState(false);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [continueWatching, setContinueWatching] = useState([]);

    const [topImdb, setTopImdb] = useState([]);
    const loadHome = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/categories`);
            const data = await res.json();
            setCategories(data.categories || []);
            const trending = data.categories?.find(c => c.id === 'trending');
            // Build carousel slides: top trending first, then take up to 5 unique items
            const slides = [];
            const seen = new Set();
            const pushUnique = (it) => {
                if (it && it.id && !seen.has(it.id)) { seen.add(it.id); slides.push(it); }
            };
            if (trending) (trending.items || []).slice(0, 5).forEach(pushUnique);
            // Fill from other categories if trending had < 5
            if (slides.length < 5) {
                for (const cat of (data.categories || [])) {
                    if (slides.length >= 5) break;
                    (cat.items || []).slice(0, 3).forEach(pushUnique);
                    if (slides.length >= 5) break;
                }
            }
            setHeroSlides(slides.slice(0, 5));
            setHero(slides[0] || null);
            setHeroIndex(0);
        } catch (err) {
            console.error('Home load failed:', err);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
        // Top IMDb row (independent of categories — falls back silently on failure)
        try {
            const ctrl = new AbortController();
            const t = setTimeout(() => ctrl.abort(), 3000);
            const r = await fetch(`${API_BASE}/top-imdb?limit=12`, { signal: ctrl.signal });
            clearTimeout(t);
            if (r.ok) {
                const j = await r.json();
                setTopImdb(j.results || []);
            }
        } catch (_) { /* ignore — Top IMDb is a nice-to-have row */ }
    }, []);

    useEffect(() => { loadHome(); }, [loadHome]);

    // Read Continue Watching from localStorage 'history' (PlayerScreen.recordProgress saves full metadata)
    const loadContinueWatching = useCallback(async () => {
        try {
            const history = Storage.get('history', {});
            const entries = Object.entries(history || {})
                .map(([id, h]) => ({ id, ...(h || {}) }))
                .filter(e => Number(e.pct) > 5 && Number(e.pct) < 95)
                .sort((a, b) => Number(b.ts || 0) - Number(a.ts || 0))
                .slice(0, 10);
            if (entries.length === 0) { setContinueWatching([]); return; }
            // Hydrate any entries missing metadata via the by-id endpoint — direct lookup
            // (avoids /search?q= failing for live-streamed titles with no searchable text).
            const hydrated = await Promise.all(entries.map(async (e) => {
                if (e.title && e.poster) return e;
                try {
                    const ctrl = new AbortController();
                    const t = setTimeout(() => ctrl.abort(), 2500);
                    const res = await fetch(`${API_BASE}/media/${encodeURIComponent(e.id)}`, { signal: ctrl.signal });
                    clearTimeout(t);
                    if (res.ok) {
                        const full = await res.json();
                        return { ...full, pct: e.pct, ts: e.ts };
                    }
                } catch (_) { /* ignore */ }
                return e;
            }));
            setContinueWatching(hydrated);
        } catch (err) {
            console.error('Continue Watching load failed:', err);
        }
    }, []);

    useEffect(() => {
        loadContinueWatching();
        const unsubscribe = navigation.addListener('focus', loadContinueWatching);
        return unsubscribe;
    }, [navigation, loadContinueWatching]);

    // Hero rotation: every 6s, pause on click or if user prefers reduced motion
    useEffect(() => {
        if (heroSlides.length <= 1 || heroPaused) return;
        let reduced = false;
        try {
            reduced = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        } catch (e) { /* ignore */ }
        if (reduced) return;
        const t = setInterval(() => {
            setHeroIndex((i) => {
                const next = (i + 1) % heroSlides.length;
                setHero(heroSlides[next]);
                return next;
            });
        }, 6000);
        return () => clearInterval(t);
    }, [heroSlides, heroPaused]);

    const onSelectMedia = useCallback((item) => {
        if (item.type === 'tv') {
            navigation.navigate('TVDetail', { item });
        } else {
            navigation.navigate('Player', { item });
        }
    }, [navigation]);

    if (loading) {
        return (
            <SafeAreaView style={styles.screen}>
                <AppHeader navigation={navigation} />
                <SkeletonGrid count={9} />
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} />
            <ScrollView showsVerticalScrollIndicator={false}>
                {hero && (
                    <TouchableOpacity
                        style={styles.heroBanner}
                        onPress={() => onSelectMedia(hero)}
                        activeOpacity={0.95}
                    >
                        <Poster url={hero.backdrop || hero.poster} title={hero.title} style={StyleSheet.absoluteFill} />
                        <View style={styles.heroOverlay}>
                            <View style={styles.heroBadge}>
                                <Text style={styles.heroBadgeText}>{hero.type === 'tv' ? 'TV SERIES' : 'FEATURED'}</Text>
                            </View>
                            <Text style={styles.heroTitle}>{hero.title}</Text>
                            <Text style={styles.heroMeta}>
                                {hero.year} {hero.rating ? `• ★ ${hero.rating}` : ''} {hero.durationMinutes ? `• ${hero.durationMinutes}m` : ''}
                            </Text>
                            <Text style={styles.heroDescription} numberOfLines={3}>{hero.description}</Text>
                            <View style={styles.heroActions}>
                                <TouchableOpacity style={styles.heroPlayButton} onPress={() => onSelectMedia(hero)}>
                                    <Text style={styles.heroPlayIcon}>▶</Text>
                                    <Text style={styles.heroPlayText}>Play</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={styles.heroWatchlistButton}
                                    onPress={() => {
                                        const list = Storage.get('watchlist', []);
                                        if (!list.includes(hero.id)) {
                                            Storage.set('watchlist', [...list, hero.id]);
                                            Alert.alert('Added', `${hero.title} added to Watchlist`);
                                        }
                                    }}
                                >
                                    <Text style={styles.heroWatchlistIcon}>+</Text>
                                    <Text style={styles.heroWatchlistText}>Watchlist</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                        {heroSlides.length > 1 && (
                            <View style={styles.heroIndicators}>
                                {heroSlides.map((_, i) => (
                                    <TouchableOpacity
                                        key={i}
                                        onPress={(e) => { e.stopPropagation && e.stopPropagation(); setHeroPaused(true); setHeroIndex(i); setHero(heroSlides[i]); }}
                                        style={[styles.heroDot, i === heroIndex && styles.heroDotActive]}
                                    />
                                ))}
                            </View>
                        )}
                    </TouchableOpacity>
                )}

                {continueWatching.length > 0 && (
                    <View style={styles.continueWatchingSection}>
                        <View style={styles.categoryHeader}>
                            <Text style={styles.categoryTitle}>Continue Watching</Text>
                            <Text style={styles.categoryMeta}>{continueWatching.length} in progress ›</Text>
                        </View>
                        <ScrollView
                            horizontal
                            showsHorizontalScrollIndicator={false}
                            contentContainerStyle={styles.continueWatchingList}
                            style={{ width: '100%' }}
                        >
                            {continueWatching.map((item, idx) => (
                                <View key={`${item.id || idx}-${idx}`} style={styles.cardSlot}>
                                    <MediaCard
                                        item={item}
                                        onPress={(m) => {
                                            if ((m.type || 'movie') === 'tv') navigation.navigate('TVDetail', { item: m });
                                            else navigation.navigate('Player', { item: m });
                                        }}
                                        showProgress
                                    />
                                </View>
                            ))}
                        </ScrollView>
                    </View>
                )}

                {topImdb.length > 0 && (
                    <View style={styles.categorySection}>
                        <View style={styles.categoryHeader}>
                            <Text style={styles.categoryTitle}>★ Top IMDb</Text>
                            <Text style={styles.categoryMeta}>{topImdb.length} titles ›</Text>
                        </View>
                        <ScrollView
                            horizontal
                            showsHorizontalScrollIndicator={false}
                            contentContainerStyle={styles.categoryList}
                            style={{ width: '100%' }}
                        >
                            {topImdb.map((item, idx) => (
                                <View key={`${item.id || idx}-${idx}`} style={styles.cardSlot}>
                                    <MediaCard item={item} onPress={onSelectMedia} />
                                </View>
                            ))}
                        </ScrollView>
                    </View>
                )}

                {categories.map(cat => (
                    <CategoryRow
                        key={cat.id}
                        category={cat}
                        onSelectMedia={onSelectMedia}
                        onSelectCategory={(c) => {
                            if (c.id === 'pak-india') {
                                navigation.navigate('Countries', { screen: 'CountryMain', params: { countryKey: 'bollywood' } });
                            } else if (c.id === 'turkish-diziler') {
                                navigation.navigate('Countries', { screen: 'CountryMain', params: { countryKey: 'turkish' } });
                            } else if (c.id === 'nollywood') {
                                navigation.navigate('Countries', { screen: 'CountryMain', params: { countryKey: 'nigerian' } });
                            } else if (c.genre) {
                                navigation.navigate('Genres', { screen: 'GenreMain', params: { genre: c.genre } });
                            } else {
                                const genreMap = {
                                    'action': 'Action', 'sci-fi': 'Sci-Fi', 'drama': 'Drama', 'comedy': 'Comedy',
                                    'thriller': 'Thriller', 'horror': 'Horror', 'romance': 'Romance', 'animation': 'Animation',
                                    'crime': 'Crime', 'mystery': 'Mystery', 'fantasy': 'Fantasy', 'documentary': 'Documentary',
                                    'biography': 'Biography', 'history': 'History'
                                };
                                const targetGenre = genreMap[c.id] || 'Action';
                                navigation.navigate('Genres', { screen: 'GenreMain', params: { genre: targetGenre } });
                            }
                        }}
                    />
                ))}

                <View style={{ height: 32 }} />
            </ScrollView>
        </SafeAreaView>
    );
}

// =================== SEARCH SCREEN ===================
function SearchScreen({ route, navigation }) {
    const parentParam = navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Search')?.params?.prefLang;
    const initialQuery = route?.params?.prefLang || parentParam || '';
    const [query, setQuery] = useState(initialQuery);
    const { width } = useWindowDimensions();
    const numCols = width >= 1400 ? 6 : width >= 1024 ? 5 : width >= 768 ? 4 : width >= 480 ? 3 : 2;
    const [typeFilter, setTypeFilter] = useState('all');
    const [searchMode, setSearchMode] = useState('curated'); // 'live' | 'curated' — default curated so search always works on first load
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const lang = route?.params?.prefLang ||
            navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Search')?.params?.prefLang;
        if (lang) {
            setQuery(lang);
        }
    }, [route?.params?.prefLang, navigation]);

    useEffect(() => {
        const unsubscribe = navigation.addListener('focus', () => {
            const lang = route?.params?.prefLang ||
                navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Search')?.params?.prefLang;
            if (lang && lang !== query) {
                setQuery(lang);
            }
        });
        return unsubscribe;
    }, [navigation, route?.params?.prefLang, query]);

    const runSearch = useCallback(async (q, type, mode) => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (q) params.set('q', q);
            if (type && type !== 'all') params.set('type', type);

            const endpoint = mode === 'live' ? `${API_BASE}/live/search?${params}` : `${API_BASE}/search?${params}`;
            let res = await fetch(endpoint);
            let data = await res.json();
            let results = data.results || [];
            // Auto-fallback: if Live mode returns 0 results for a query, try Curated
            if (mode === 'live' && q && results.length === 0) {
                try {
                    const fallbackRes = await fetch(`${API_BASE}/search?${params}`);
                    const fallbackData = await fallbackRes.json();
                    const fallbackResults = fallbackData.results || [];
                    if (fallbackResults.length > 0) {
                        results = fallbackResults.map(r => ({ ...r, sourceOrigin: 'curated', _fallback: true }));
                    }
                } catch (fbErr) {
                    console.error('Curated fallback failed:', fbErr);
                }
            }
            setResults(results);
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const t = setTimeout(() => runSearch(query, typeFilter, searchMode), 250);
        return () => clearTimeout(t);
    }, [query, typeFilter, searchMode, runSearch]);

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} title="Search" />
            {/* Live vs Curated Mode Switcher */}
            <View style={styles.searchModeRow}>
                <TouchableOpacity
                    style={[styles.searchModeTab, searchMode === 'live' && styles.searchModeTabActive]}
                    onPress={() => setSearchMode('live')}
                >
                    <Text style={[styles.searchModeText, searchMode === 'live' && styles.searchModeTextActive]}>
                        ⚡ Live (All 10 Sources)
                    </Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.searchModeTab, searchMode === 'curated' && styles.searchModeTabActive]}
                    onPress={() => setSearchMode('curated')}
                >
                    <Text style={[styles.searchModeText, searchMode === 'curated' && styles.searchModeTextActive]}>
                        📚 Curated (Fast)
                    </Text>
                </TouchableOpacity>
            </View>

            <View style={styles.searchBar}>
                <Text style={styles.searchIcon}>🔍</Text>
                <TextInput
                    style={styles.searchInput}
                    placeholder={searchMode === 'live' ? 'Search live across 100k+ titles...' : 'Search curated catalog...'}
                    placeholderTextColor={COLORS.textMuted}
                    value={query}
                    onChangeText={setQuery}
                    autoCorrect={false}
                />
                {query.length > 0 && (
                    <TouchableOpacity onPress={() => setQuery('')}>
                        <Text style={styles.clearButton}>✕</Text>
                    </TouchableOpacity>
                )}
            </View>
            <View style={styles.filterRow}>
                {['all', 'movie', 'tv'].map(t => (
                    <TouchableOpacity
                        key={t}
                        style={[styles.filterChip, typeFilter === t && styles.filterChipActive]}
                        onPress={() => setTypeFilter(t)}
                    >
                        <Text style={[styles.filterChipText, typeFilter === t && styles.filterChipTextActive]}>
                            {t === 'all' ? 'All' : t === 'movie' ? 'Movies' : 'TV Shows'}
                        </Text>
                    </TouchableOpacity>
                ))}
                <Text style={styles.resultCount}>
                    {results.length} results {searchMode === 'live' ? '(Live)' : '(Curated)'}
                </Text>
            </View>

            {loading ? (
                <View style={{ flex: 1, padding: 16 }}>
                    {searchMode === 'live' && (
                        <View style={styles.liveProgressBanner}>
                            <ActivityIndicator size="small" color={COLORS.brand} style={{ marginRight: 8 }} />
                            <Text style={styles.liveProgressText}>Querying live scrapers & SQLite cache...</Text>
                        </View>
                    )}
                    <SkeletonGrid count={6} />
                </View>
            ) : (
                <FlatList
                    data={results}
                    keyExtractor={(item) => item.id}
                    numColumns={numCols}
                    contentContainerStyle={styles.searchGrid}
                    columnWrapperStyle={styles.searchRow}
                    renderItem={({ item }) => (
                        <MediaCard
                            item={item}
                            onPress={(m) => {
                                if (m.type === 'tv') navigation.navigate('TVDetail', { item: m });
                                else navigation.navigate('Player', { item: m });
                            }}
                            showProgress
                        />
                    )}
                    ListEmptyComponent={
                        <View style={styles.emptyState}>
                            <Text style={styles.emptyIcon}>🔍</Text>
                            <Text style={styles.emptyTitle}>No results</Text>
                            <Text style={styles.emptySubtitle}>Try a different search term or toggle Live/Curated</Text>
                        </View>
                    }
                />
            )}
        </SafeAreaView>
    );
}

// =================== WATCHLIST SCREEN ===================
function WatchlistScreen({ navigation }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const { width } = useWindowDimensions();
    const numCols = width >= 1400 ? 6 : width >= 1024 ? 5 : width >= 768 ? 4 : width >= 480 ? 3 : 2;

    const loadWatchlist = useCallback(async () => {
        const ids = Storage.get('watchlist', []);
        if (ids.length === 0) {
            setItems([]);
            setLoading(false);
            return;
        }
        try {
            const res = await fetch(`${API_BASE}/search?q=`);
            const data = await res.json();
            const all = data.results || [];
            const filtered = ids.map(id => all.find(m => m.id === id)).filter(Boolean);
            setItems(filtered);
        } catch (err) {
            console.error('Watchlist load failed:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const unsubscribe = navigation.addListener('focus', loadWatchlist);
        return unsubscribe;
    }, [navigation, loadWatchlist]);

    if (loading) {
        return (
            <SafeAreaView style={styles.screen}>
                <SkeletonGrid count={6} />
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} title="Watchlist" />
            <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>My Watchlist</Text>
                {items.length > 0 && (
                    <TouchableOpacity onPress={() => { Storage.set('watchlist', []); setItems([]); }}>
                        <Text style={styles.clearText}>Clear all</Text>
                    </TouchableOpacity>
                )}
            </View>
            {items.length === 0 ? (
                <View style={styles.emptyState}>
                    <Text style={styles.emptyIcon}>📺</Text>
                    <Text style={styles.emptyTitle}>Your watchlist is empty</Text>
                    <Text style={styles.emptySubtitle}>Add titles to watch them later</Text>
                </View>
            ) : (
                <FlatList
                    data={items}
                    keyExtractor={(item) => item.id}
                    numColumns={numCols}
                    contentContainerStyle={styles.searchGrid}
                    columnWrapperStyle={styles.searchRow}
                    renderItem={({ item }) => (
                        <MediaCard
                            item={item}
                            onPress={(m) => {
                                if (m.type === 'tv') navigation.navigate('TVDetail', { item: m });
                                else navigation.navigate('Player', { item: m });
                            }}
                            showProgress
                        />
                    )}
                />
            )}
        </SafeAreaView>
    );
}

// =================== BROWSE BY COUNTRY SCREEN ===================
function CountryScreen({ route, navigation }) {
    const parentParam = navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Countries')?.params?.countryKey;
    const initialCountryKey = route?.params?.countryKey || parentParam || 'all';
    const { width } = useWindowDimensions();
    const numCols = width >= 1400 ? 6 : width >= 1024 ? 5 : width >= 768 ? 4 : width >= 480 ? 3 : 2;
    const [countries, setCountries] = useState([]);
    const [active, setActive] = useState(initialCountryKey);
    const [items, setItems] = useState([]);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);

    useEffect(() => {
        const load = async () => {
            try {
                const r = await fetch(`${API_BASE}/countries`);
                const j = await r.json();
                setCountries(j.countries || []);
            } catch (e) { console.error(e); }
        };
        load();
    }, []);

    // Sync active country when route.params or parent route params change
    useEffect(() => {
        const paramKey = route?.params?.countryKey ||
            navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Countries')?.params?.countryKey;
        if (paramKey && paramKey !== active) {
            setActive(paramKey);
        }
    }, [route?.params?.countryKey, active, navigation]);

    // Sync on navigation focus
    useEffect(() => {
        const unsubscribe = navigation.addListener('focus', () => {
            const paramKey = route?.params?.countryKey ||
                navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Countries')?.params?.countryKey;
            if (paramKey && paramKey !== active) {
                setActive(paramKey);
            }
        });
        return unsubscribe;
    }, [navigation, route?.params?.countryKey, active]);

    const loadCountryItems = useCallback(async (cKey, pageNum = 1, append = false) => {
        if (pageNum === 1) setLoading(true);
        else setLoadingMore(true);

        try {
            let fetchedItems = [];
            // Try live country endpoint first (with 2.5s AbortController)
            try {
                const ctrl = new AbortController();
                const timeoutId = setTimeout(() => ctrl.abort(), 2500);
                const res = await fetch(`${API_BASE}/live/country/${cKey}?page=${pageNum}&limit=50`, { signal: ctrl.signal });
                clearTimeout(timeoutId);
                if (res.ok) {
                    const data = await res.json();
                    fetchedItems = data.results || [];
                }
            } catch (e) {}

            // Fallback to /search?country=  (live=false so backend skips live lane)
            if (fetchedItems.length === 0 && pageNum === 1) {
                try {
                    const r = await fetch(`${API_BASE}/search?country=${encodeURIComponent(cKey)}&live=false`);
                    const j = await r.json();
                    fetchedItems = j.results || [];
                } catch (e) {
                    fetchedItems = [];
                }
            }

            if (append) {
                setItems(prev => {
                    const existingIds = new Set(prev.map(p => p.id));
                    const newUnique = fetchedItems.filter(f => !existingIds.has(f.id));
                    return [...prev, ...newUnique];
                });
            } else {
                setItems(fetchedItems);
            }
            setHasMore(fetchedItems.length >= 40);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, []);

    useEffect(() => {
        setPage(1);
        loadCountryItems(active, 1, false);
    }, [active, loadCountryItems]);

    const handleLoadMore = () => {
        if (!loading && !loadingMore && hasMore) {
            const nextPage = page + 1;
            setPage(nextPage);
            loadCountryItems(active, nextPage, true);
        }
    };

    const activeCountry = countries.find(c => c.key === active);

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} title="Countries" />
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.countryBar}>
                {countries.map(c => (
                    <TouchableOpacity
                        key={c.key}
                        style={[styles.countryChip, active === c.key && styles.countryChipActive]}
                        onPress={() => {
                            setActive(c.key);
                            try { navigation.setParams({ countryKey: c.key }); } catch (e) {}
                        }}
                    >
                        <Text style={[styles.countryFlag, active === c.key && styles.countryFlagActive]}>{c.flag}</Text>
                        <Text style={[styles.countryLabel, active === c.key && styles.countryLabelActive]}>{c.label}</Text>
                        <Text style={[styles.countryCount, active === c.key && styles.countryCountActive]}>{c.count}</Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>
            <View style={styles.browseHeader}>
                <Text style={styles.browseTitle}>
                    {activeCountry ? `${activeCountry.flag} ${activeCountry.label}` : 'All Countries'}
                </Text>
                <Text style={styles.browseSubtitle}>
                    {items.length} {items.length === 1 ? 'title' : 'titles'} • {activeCountry?.code || ''} (Live Catalog)
                </Text>
            </View>
            {loading ? <SkeletonGrid count={6} /> : (
                <FlatList
                    data={items}
                    keyExtractor={(item) => item.id}
                    numColumns={numCols}
                    contentContainerStyle={styles.searchGrid}
                    columnWrapperStyle={styles.searchRow}
                    onEndReached={handleLoadMore}
                    onEndReachedThreshold={0.5}
                    ListFooterComponent={loadingMore ? <ActivityIndicator size="small" color={COLORS.brand} style={{ marginVertical: 16 }} /> : null}
                    renderItem={({ item }) => (
                        <MediaCard
                            item={item}
                            onPress={(m) => {
                                if (m.type === 'tv') navigation.navigate('TVDetail', { item: m });
                                else navigation.navigate('Player', { item: m });
                            }}
                        />
                    )}
                    ListEmptyComponent={
                        <View style={styles.emptyState}>
                            <Text style={styles.emptyIcon}>🎬</Text>
                            <Text style={styles.emptyTitle}>No titles in this country</Text>
                            <Text style={styles.emptySubtitle}>Try another country from the bar above</Text>
                        </View>
                    }
                />
            )}
        </SafeAreaView>
    );
}

// =================== BROWSE BY GENRE SCREEN ===================
function GenreScreen({ route, navigation }) {
    const genres = [
        'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime',
        'Drama', 'Fantasy', 'Horror', 'Music', 'Mystery', 'Romance',
        'Sci-Fi', 'Thriller', 'Documentary', 'Family', 'History', 'War'
    ];
    const parentParam = navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Genres')?.params?.genre;
    const initialGenre = route?.params?.genre || parentParam || 'Action';
    const [active, setActive] = useState(initialGenre);
    const { width } = useWindowDimensions();
    const numCols = width >= 1400 ? 6 : width >= 1024 ? 5 : width >= 768 ? 4 : width >= 480 ? 3 : 2;
    const [items, setItems] = useState([]);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loading, setLoading] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);

    // Sync active genre when route.params or parent route params change
    useEffect(() => {
        const paramGenre = route?.params?.genre ||
            navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Genres')?.params?.genre;
        if (paramGenre && paramGenre !== active) {
            setActive(paramGenre);
        }
    }, [route?.params?.genre, active, navigation]);

    // Sync on navigation focus
    useEffect(() => {
        const unsubscribe = navigation.addListener('focus', () => {
            const paramGenre = route?.params?.genre ||
                navigation.getParent()?.getState()?.routes?.find(r => r.name === 'Genres')?.params?.genre;
            if (paramGenre && paramGenre !== active) {
                setActive(paramGenre);
            }
        });
        return unsubscribe;
    }, [navigation, route?.params?.genre, active]);

    const loadGenreItems = useCallback(async (g, pageNum = 1, append = false) => {
        if (pageNum === 1) setLoading(true);
        else setLoadingMore(true);

        try {
            let fetchedItems = [];
            let liveUsed = false;
            try {
                const ctrl = new AbortController();
                const timeoutId = setTimeout(() => ctrl.abort(), 2500);
                const res = await fetch(`${API_BASE}/live/genre/${encodeURIComponent(g)}?page=${pageNum}&limit=50`, { signal: ctrl.signal });
                clearTimeout(timeoutId);
                if (res.ok) {
                    const data = await res.json();
                    fetchedItems = data.results || [];
                    liveUsed = (data.live === true || data.liveAvailable === true);
                }
            } catch (e) {}

            if (fetchedItems.length === 0 && pageNum === 1) {
                try {
                    const r = await fetch(`${API_BASE}/search?genre=${encodeURIComponent(g)}&live=false`);
                    const j = await r.json();
                    fetchedItems = j.results || [];
                } catch (e) {
                    fetchedItems = [];
                }
            }

            if (append) {
                setItems(prev => {
                    const existingIds = new Set(prev.map(p => p.id));
                    const newUnique = fetchedItems.filter(f => !existingIds.has(f.id));
                    return [...prev, ...newUnique];
                });
            } else {
                setItems(fetchedItems);
            }
            setHasMore(fetchedItems.length >= 40);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, []);

    useEffect(() => {
        setPage(1);
        loadGenreItems(active, 1, false);
    }, [active, loadGenreItems]);

    const handleLoadMore = () => {
        if (!loading && !loadingMore && hasMore) {
            const nextPage = page + 1;
            setPage(nextPage);
            loadGenreItems(active, nextPage, true);
        }
    };

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} title="Genres" />
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.countryBar}>
                {genres.map(g => (
                    <TouchableOpacity
                        key={g}
                        style={[styles.countryChip, active === g && styles.countryChipActive]}
                        onPress={() => {
                            setActive(g);
                            try { navigation.setParams({ genre: g }); } catch (e) {}
                        }}
                    >
                        <Text style={[styles.countryLabel, active === g && styles.countryLabelActive]}>{g}</Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>
            <View style={styles.browseHeader}>
                <Text style={styles.browseTitle}>{active} Movies</Text>
                <Text style={styles.browseSubtitle}>{items.length} titles (Live Catalog)</Text>
            </View>
            {loading ? <SkeletonGrid count={6} /> : (
                <FlatList
                    data={items}
                    keyExtractor={(item) => item.id}
                    numColumns={numCols}
                    contentContainerStyle={styles.searchGrid}
                    columnWrapperStyle={styles.searchRow}
                    onEndReached={handleLoadMore}
                    onEndReachedThreshold={0.5}
                    ListFooterComponent={loadingMore ? <ActivityIndicator size="small" color={COLORS.brand} style={{ marginVertical: 16 }} /> : null}
                    renderItem={({ item }) => (
                        <MediaCard
                            item={item}
                            onPress={(m) => {
                                if (m.type === 'tv') navigation.navigate('TVDetail', { item: m });
                                else navigation.navigate('Player', { item: m });
                            }}
                        />
                    )}
                    ListEmptyComponent={
                        <View style={styles.emptyState}>
                            <Text style={styles.emptyIcon}>🎭</Text>
                            <Text style={styles.emptyTitle}>No titles</Text>
                        </View>
                    }
                />
            )}
        </SafeAreaView>
    );
}

// =================== SETTINGS SCREEN ===================
function SettingsScreen({ navigation }) {
    const [sourcePreference, setSourcePreference] = useState(Storage.get('pref_source', 'vidsrc'));
    const [autoplay, setAutoplay] = useState(Storage.get('pref_autoplay', true));
    const [watchlistCount, setWatchlistCount] = useState(Storage.get('watchlist', []).length);
    const [historyCount, setHistoryCount] = useState(Object.keys(Storage.get('history', {})).length);

    const updatePref = (key, value) => {
        Storage.set(key, value);
        if (key === 'pref_source') setSourcePreference(value);
        if (key === 'pref_autoplay') setAutoplay(value);
    };

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} title="Settings" />
            <ScrollView contentContainerStyle={styles.settingsContent}>
                <Text style={styles.settingsTitle}>Settings</Text>

                <View style={styles.settingsCard}>
                    <Text style={styles.settingsCardTitle}>Default Source</Text>
                    <Text style={styles.settingsCardSubtitle}>Priority order for stream mirrors</Text>
                    <View style={styles.sourceChips}>
                        {['vidsrc', 'superembed', 'multiembed'].map(s => (
                            <TouchableOpacity
                                key={s}
                                style={[styles.sourceChip, sourcePreference === s && styles.sourceChipActive]}
                                onPress={() => updatePref('pref_source', s)}
                            >
                                <Text style={[styles.sourceChipText, sourcePreference === s && styles.sourceChipTextActive]}>
                                    {s === 'vidsrc' ? 'VidSrc' : s === 'superembed' ? 'SuperEmbed' : 'MultiEmbed'}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>

                <View style={styles.settingsCard}>
                    <Text style={styles.settingsCardTitle}>Playback</Text>
                    <View style={styles.settingRow}>
                        <Text style={styles.settingLabel}>Autoplay next episode</Text>
                        <TouchableOpacity
                            style={[styles.toggle, autoplay && styles.toggleOn]}
                            onPress={() => updatePref('pref_autoplay', !autoplay)}
                        >
                            <View style={[styles.toggleKnob, autoplay && styles.toggleKnobOn]} />
                        </TouchableOpacity>
                    </View>
                </View>

                <View style={styles.settingsCard}>
                    <Text style={styles.settingsCardTitle}>Library</Text>
                    <View style={styles.statRow}>
                        <Text style={styles.statLabel}>Watchlist titles</Text>
                        <Text style={styles.statValue}>{watchlistCount}</Text>
                    </View>
                    <View style={styles.statRow}>
                        <Text style={styles.statLabel}>Continue watching</Text>
                        <Text style={styles.statValue}>{historyCount}</Text>
                    </View>
                    <TouchableOpacity
                        style={styles.dangerButton}
                        onPress={() => {
                            Alert.alert('Clear All Data', 'Remove watchlist and history?', [
                                { text: 'Cancel', style: 'cancel' },
                                {
                                    text: 'Clear',
                                    style: 'destructive',
                                    onPress: () => {
                                        Storage.remove('watchlist');
                                        Storage.remove('history');
                                        setWatchlistCount(0);
                                        setHistoryCount(0);
                                    }
                                }
                            ]);
                        }}
                    >
                        <Text style={styles.dangerButtonText}>Clear watchlist & history</Text>
                    </TouchableOpacity>
                </View>

                <View style={styles.settingsCard}>
                    <Text style={styles.settingsCardTitle}>About</Text>
                    <Text style={styles.settingsCardBody}>
                        StreamApp v1.0.0{'\n'}
                        Cross-Platform Legal Streaming Aggregator{'\n\n'}
                        Sources: VidSrc, SuperEmbed, MultiEmbed, plus a 17-title legal fallback catalog (Blender Open Movies, Archive.org, NASA).{'\n\n'}
                        Streams are fetched from public embed services. All metadata via TMDB CDN.
                    </Text>
                </View>
            </ScrollView>
        </SafeAreaView>
    );
}

// =================== PLAYER SCREEN (movie & tv episode) ===================
function buildMirrors(item) {
    const mirrors = [];
    const tId = item.tmdbId;
    const iId = item.imdbId;
    const s = item.season;
    const e = item.episode;
    const cleanTitle = (item.title || '').replace(/\s*-\s*S\d+E\d+.*$/i, '').trim();

    // 1. VidSrc.me (The #1 most reliable VidSrc server)
    if (tId) {
        if (s && e) {
            mirrors.push({ label: 'VidSrc.me (Primary)', provider: 'vidsrc', url: `https://vidsrc.me/embed/tv?tmdb=${tId}&season=${s}&episode=${e}`, quality: '1080p' });
        } else {
            mirrors.push({ label: 'VidSrc.me (Primary)', provider: 'vidsrc', url: `https://vidsrc.me/embed/movie?tmdb=${tId}`, quality: '1080p' });
        }
    } else if (iId) {
        if (s && e) {
            mirrors.push({ label: 'VidSrc.me (Primary)', provider: 'vidsrc', url: `https://vidsrc.me/embed/tv?imdb=${iId}&season=${s}&episode=${e}`, quality: '1080p' });
        } else {
            mirrors.push({ label: 'VidSrc.me (Primary)', provider: 'vidsrc', url: `https://vidsrc.me/embed/movie?imdb=${iId}`, quality: '1080p' });
        }
    }

    // 2. SuperEmbed (multiembed.mov - fast & reliable)
    const superId = tId || iId;
    if (superId) {
        const tmdbParam = tId ? '&tmdb=1' : '';
        if (s && e) {
            mirrors.push({ label: 'SuperEmbed (Fast)', provider: 'superembed', url: `https://multiembed.mov/?video_id=${superId}${tmdbParam}&s=${s}&e=${e}`, quality: '1080p' });
        } else {
            mirrors.push({ label: 'SuperEmbed (Fast)', provider: 'superembed', url: `https://multiembed.mov/?video_id=${superId}${tmdbParam}`, quality: '1080p' });
        }
    }

    // 3. VidSrc.to (Alternative)
    if (tId || iId) {
        const vId = tId || iId;
        if (s && e) {
            mirrors.push({ label: 'VidSrc.to (Mirror 2)', provider: 'vidsrc', url: `https://vidsrc.to/embed/tv/${vId}/${s}/${e}`, quality: '1080p' });
        } else {
            mirrors.push({ label: 'VidSrc.to (Mirror 2)', provider: 'vidsrc', url: `https://vidsrc.to/embed/movie/${vId}`, quality: '1080p' });
        }
    }

    // 4. 2Embed (2embed.cc)
    if (tId || iId) {
        const embId = tId || iId;
        if (s && e) {
            mirrors.push({ label: '2Embed (Mirror 3)', provider: '2embed', url: `https://www.2embed.cc/embedtv/${embId}&s=${s}&e=${e}`, quality: '720p' });
        } else {
            mirrors.push({ label: '2Embed (Mirror 3)', provider: '2embed', url: `https://www.2embed.cc/embed/${embId}`, quality: '720p' });
        }
    }

    // 5. Official HD Stream via YouTube (100% Guaranteed Playback for Pakistani Serials & National Titles)
    if (cleanTitle) {
        const ytQuery = s && e
            ? `${cleanTitle} Episode ${e} full episode HD`
            : `${cleanTitle} full movie HD`;
        mirrors.push({
            label: 'YouTube (Official HD)',
            provider: 'youtube',
            url: `https://www.youtube-nocookie.com/embed?listType=search&list=${encodeURIComponent(ytQuery)}`,
            quality: '1080p'
        });
    }

    // Append any extra streams passed in item.streams, ignoring dead vidsrc.xyz or 404 directstream
    if (Array.isArray(item.streams)) {
        for (const st of item.streams) {
            if (st && st.url && !st.url.includes('vidsrc.xyz') && !st.url.includes('directstream.php') && !mirrors.some(m => m.url === st.url)) {
                mirrors.push(st);
            }
        }
    }
    return mirrors;
}

function PlayerScreen({ route, navigation }) {
    const { item } = route.params;
    // Bump view counter once per Player mount so popular titles surface in local ranking.
    try { Storage.bump(`views_${item.id}`, 1); } catch (_) { /* ignore */ }
    const initialMirrors = buildMirrors(item);
    const [streamSources, setStreamSources] = useState(initialMirrors);
    const [activeSourceIdx, setActiveSourceIdx] = useState(0);
    const [streamUrl, setStreamUrl] = useState(initialMirrors[0]?.url || null);
    const [loading, setLoading] = useState(initialMirrors.length === 0);
    const [error, setError] = useState(null);
    const [inWatchlist, setInWatchlist] = useState(false);
    const [iframeLoaded, setIframeLoaded] = useState(false);
    const fallbackTimer = useRef(null);

    useEffect(() => {
        setInWatchlist(Storage.get('watchlist', []).includes(item.id));
    }, [item.id]);

    const loadPrimaryStream = useCallback(async () => {
        if (initialMirrors.length > 0 && initialMirrors[0]?.url) {
            setStreamUrl(prev => prev || initialMirrors[0].url);
            setLoading(false);
        } else {
            setLoading(true);
        }

        setError(null);
        try {
            const res = await fetch(`${API_BASE}/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: item.sourceUrl || item.id,
                    sourceName: item.sourceName || item.source,
                    title: item.title,
                    tmdbId: item.tmdbId,
                    imdbId: item.imdbId,
                    season: item.season,
                    episode: item.episode
                })
            });
            const data = await res.json();
            if (data.status === 'success' && data.streamUrl) {
                setStreamUrl(data.streamUrl);
                if (Array.isArray(data.streams) && data.streams.length > 0) {
                    // Filter out dead vidsrc.xyz or 404 directstream
                    const validStreams = data.streams.filter(st => st && st.url && !st.url.includes('vidsrc.xyz') && !st.url.includes('directstream.php'));
                    // Ensure YouTube HD mirror is present
                    const ytMirror = initialMirrors.find(m => m.provider === 'youtube');
                    if (ytMirror && !validStreams.some(s => s.provider === 'youtube')) {
                        validStreams.push(ytMirror);
                    }
                    setStreamSources(validStreams);
                }
            } else if (initialMirrors.length > 0 && initialMirrors[0]?.url) {
                setStreamUrl(initialMirrors[0].url);
            } else {
                setError(data.error || 'No stream available');
            }
        } catch (err) {
            if (initialMirrors.length > 0 && initialMirrors[0]?.url) {
                setStreamUrl(initialMirrors[0].url);
            } else {
                setError(`Network error: ${err.message}`);
            }
        } finally {
            setLoading(false);
        }
    }, [item.id, item.title, item.tmdbId, item.imdbId, item.season, item.episode, item.sourceUrl, item.sourceName, item.source, initialMirrors]);

    useEffect(() => {
        loadPrimaryStream();
    }, [loadPrimaryStream]);

    const swapToSource = (idx) => {
        if (!streamSources[idx]?.url) return;
        setActiveSourceIdx(idx);
        setStreamUrl(streamSources[idx].url);
        setError(null);
    };

    const nextMirror = () => {
        if (streamSources.length <= 1) return;
        const nextIdx = (activeSourceIdx + 1) % streamSources.length;
        swapToSource(nextIdx);
    };

    const toggleWatchlist = () => {
        const list = Storage.get('watchlist', []);
        const newList = list.includes(item.id)
            ? list.filter(id => id !== item.id)
            : [...list, item.id];
        Storage.set('watchlist', newList);
        setInWatchlist(!inWatchlist);
    };

    const recordProgress = (pct) => {
        const history = Storage.get('history', {});
        const entry = { pct, ts: Date.now(), title: item.title, type: item.type, poster: item.poster, backdrop: item.backdrop, year: item.year, rating: item.rating, sourceName: item.sourceName || item.source, sourceUrl: item.sourceUrl || item.id, tmdbId: item.tmdbId, imdbId: item.imdbId };
        history[item.id] = entry;
        Storage.set('history', history);
        Storage.set(`meta_${item.id}`, { id: item.id, ...entry });
    };

    useEffect(() => {
        if (!streamUrl) return;
        setIframeLoaded(false);
        const t = setTimeout(() => recordProgress(15), 8000);
        return () => clearTimeout(t);
    }, [streamUrl]);

    // Auto-advance to next mirror if iframe never loads within 12s
    useEffect(() => {
        if (!streamUrl || iframeLoaded) {
            if (fallbackTimer.current) { clearTimeout(fallbackTimer.current); fallbackTimer.current = null; }
            return;
        }
        if (fallbackTimer.current) clearTimeout(fallbackTimer.current);
        fallbackTimer.current = setTimeout(() => {
            if (!iframeLoaded && streamSources.length > 1) {
                setStreamSources(prev => prev); // ensure closure freshness
                const nextIdx = (activeSourceIdx + 1) % streamSources.length;
                if (nextIdx !== activeSourceIdx) {
                    swapToSource(nextIdx);
                }
            }
        }, 12000);
        return () => {
            if (fallbackTimer.current) { clearTimeout(fallbackTimer.current); fallbackTimer.current = null; }
        };
    }, [streamUrl, iframeLoaded, activeSourceIdx, streamSources.length]);

    // Cleanup on unmount
    useEffect(() => {
        return () => { if (fallbackTimer.current) { clearTimeout(fallbackTimer.current); fallbackTimer.current = null; } };
    }, []);

    if (loading) {
        return (
            <SafeAreaView style={styles.screen}>
                <View style={styles.playerLoadingContainer}>
                    <ActivityIndicator size="large" color={COLORS.brand} />
                    <Text style={styles.loadingText}>Resolving stream…</Text>
                    <Text style={styles.loadingSubtext}>Trying {streamSources.length || 1} sources</Text>
                </View>
            </SafeAreaView>
        );
    }

    if (error && !streamUrl) {
        return (
            <SafeAreaView style={styles.screen}>
                <View style={styles.errorState}>
                    <Text style={styles.errorIcon}>⚠️</Text>
                    <Text style={styles.errorTitle}>Playback unavailable</Text>
                    <Text style={styles.errorMessage}>{error}</Text>
                    {streamSources.length > 1 && (
                        <TouchableOpacity style={[styles.retryButton, { backgroundColor: COLORS.accent, marginBottom: 10 }]} onPress={nextMirror}>
                            <Text style={[styles.retryButtonText, { color: '#000' }]}>Try Next Mirror ({streamSources[(activeSourceIdx + 1) % streamSources.length]?.label})</Text>
                        </TouchableOpacity>
                    )}
                    <TouchableOpacity style={styles.retryButton} onPress={loadPrimaryStream}>
                        <Text style={styles.retryButtonText}>Try again</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
                        <Text style={styles.backButtonText}>Back</Text>
                    </TouchableOpacity>
                </View>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.screen}>
            <View style={styles.playerWrapper}>
                {/* Real iframe-based embed player with remount key */}
                {Platform.OS === 'web' ? (
                    <iframe
                        key={streamUrl}
                        src={streamUrl}
                        onLoad={() => setIframeLoaded(true)}
                        style={{
                            width: '100%',
                            height: '100%',
                            border: 'none',
                            backgroundColor: '#000'
                        }}
                        allowFullScreen
                        allow="autoplay; encrypted-media; picture-in-picture"
                    />
                ) : (
                    <View style={styles.iframeFallback}>
                        <Poster url={item.backdrop || item.poster} title={item.title} style={StyleSheet.absoluteFill} />
                        <View style={styles.iframeFallbackOverlay}>
                            <Text style={styles.iframeFallbackText}>
                                Embed player requires native WebView (use web build for now)
                            </Text>
                        </View>
                    </View>
                )}
            </View>

            {streamSources.length > 0 && (
                <View style={styles.switchMirrorContainer}>
                    <TouchableOpacity
                        style={styles.switchMirrorBanner}
                        onPress={nextMirror}
                        activeOpacity={0.8}
                    >
                        <Text style={styles.switchMirrorText}>
                            ⚡ Mirror {activeSourceIdx + 1} of {streamSources.length}: <Text style={{ fontWeight: 'bold' }}>{streamSources[activeSourceIdx]?.label || 'Mirror'}</Text> (Tap to switch)
                        </Text>
                    </TouchableOpacity>
                    {Platform.OS === 'web' && streamUrl && (
                        <TouchableOpacity
                            style={styles.openExternalTabBtn}
                            onPress={() => window.open(streamUrl, '_blank')}
                            activeOpacity={0.8}
                        >
                            <Text style={styles.openExternalTabText}>↗ New Tab</Text>
                        </TouchableOpacity>
                    )}
                </View>
            )}

            <ScrollView style={styles.playerDetails} contentContainerStyle={styles.playerDetailsContent}>
                <View style={styles.playerHeader}>
                    <View style={{ flex: 1 }}>
                        <Text style={styles.playerTitle}>{item.title}</Text>
                        <Text style={styles.playerSubtitle}>
                            {item.year} {item.rating ? `• ★ ${item.rating}` : ''}
                            {item.durationMinutes ? ` • ${item.durationMinutes}m` : ''}
                        </Text>
                    </View>
                    <TouchableOpacity onPress={toggleWatchlist} style={styles.watchlistBtn}>
                        <Text style={[styles.watchlistBtnText, inWatchlist && styles.watchlistBtnActive]}>
                            {inWatchlist ? '✓ In Watchlist' : '+ Watchlist'}
                        </Text>
                    </TouchableOpacity>
                </View>

                <Text style={styles.description}>{item.description}</Text>

                <View style={styles.metaGrid}>
                    <View style={styles.metaItem}>
                        <Text style={styles.metaLabel}>Genres</Text>
                        <Text style={styles.metaValue}>{(item.genres || []).join(', ')}</Text>
                    </View>
                    {item.imdbId && (
                        <View style={styles.metaItem}>
                            <Text style={styles.metaLabel}>IMDb</Text>
                            <Text style={styles.metaValue}>{item.imdbId}</Text>
                        </View>
                    )}
                </View>

                <View style={styles.sourcesCard}>
                    <Text style={styles.sourcesTitle}>Sources & Mirrors ({streamSources.length})</Text>
                    <Text style={styles.sourcesSubtitle}>Tap any mirror to switch if current player is blocked or unavailable</Text>
                    {streamSources.map((s, idx) => (
                        <TouchableOpacity
                            key={idx}
                            style={[styles.sourceRow, activeSourceIdx === idx && styles.sourceRowActive]}
                            onPress={() => swapToSource(idx)}
                        >
                            <View style={{ flex: 1 }}>
                                <Text style={styles.sourceLabel}>{s.label}</Text>
                                <Text style={styles.sourceMeta}>{s.provider} • {s.quality || '1080p'}</Text>
                            </View>
                            {activeSourceIdx === idx && <Text style={styles.sourceCheck}>● Active</Text>}
                        </TouchableOpacity>
                    ))}
                </View>

                <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
                    <Text style={styles.backButtonText}>Back to library</Text>
                </TouchableOpacity>
            </ScrollView>
        </SafeAreaView>
    );
}

// =================== TV SHOW DETAIL SCREEN ===================
function TVDetailScreen({ route, navigation }) {
    const { item } = route.params;
    const [season, setSeason] = useState(1);
    const [episodes, setEpisodes] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                const targetId = encodeURIComponent(item.tmdbId || item.imdbId || item.id);
                const showTitle = encodeURIComponent(item.title || '');
                const res = await fetch(`${API_BASE}/tv/${targetId}/episodes?season=${season}&title=${showTitle}`);
                const data = await res.json();
                setEpisodes(data.episodes || []);
            } catch (err) {
                console.error('Episodes load failed:', err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [item.tmdbId, item.imdbId, item.id, season]);

    const playEpisode = (ep) => {
        navigation.navigate('Player', {
            item: {
                ...item,
                season: ep.season,
                episode: ep.episode,
                title: `${item.title} - S${ep.season}E${ep.episode}`,
                streams: ep.sources || [],
                durationMinutes: item.durationMinutes
            }
        });
    };

    return (
        <SafeAreaView style={styles.screen}>
            <ScrollView>
                <View style={styles.tvHeader}>
                    <Poster url={item.backdrop || item.poster} title={item.title} style={styles.tvHeaderPoster} />
                    <View style={styles.tvHeaderOverlay}>
                        <View style={styles.heroBadge}>
                            <Text style={styles.heroBadgeText}>TV SERIES</Text>
                        </View>
                        <Text style={styles.playerTitle}>{item.title}</Text>
                        <Text style={styles.playerSubtitle}>
                            {item.year} {item.rating ? `• ★ ${item.rating}` : ''}
                        </Text>
                        <Text style={styles.description} numberOfLines={4}>{item.description}</Text>
                    </View>
                </View>

                <View style={styles.seasonSelector}>
                    <Text style={styles.sectionTitle}>Season</Text>
                    <FlatList
                        horizontal
                        data={Array.from({ length: item.seasons || 1 }, (_, i) => i + 1)}
                        keyExtractor={(s) => `s${s}`}
                        showsHorizontalScrollIndicator={false}
                        renderItem={({ item: s }) => (
                            <TouchableOpacity
                                style={[styles.seasonChip, season === s && styles.seasonChipActive]}
                                onPress={() => setSeason(s)}
                            >
                                <Text style={[styles.seasonChipText, season === s && styles.seasonChipTextActive]}>
                                    Season {s}
                                </Text>
                            </TouchableOpacity>
                        )}
                    />
                </View>

                {loading ? (
                    <SkeletonGrid count={4} />
                ) : (
                    <View style={styles.episodesList}>
                        {episodes.map(ep => (
                            <TouchableOpacity
                                key={`${ep.season}-${ep.episode}`}
                                style={styles.episodeRow}
                                onPress={() => playEpisode(ep)}
                            >
                                <View style={styles.episodeNumber}>
                                    <Text style={styles.episodeNumberText}>{ep.episode}</Text>
                                </View>
                                <View style={{ flex: 1 }}>
                                    <Text style={styles.episodeTitle}>{ep.title}</Text>
                                    <Text style={styles.episodeMeta}>{ep.sources.length} sources available</Text>
                                </View>
                                <Text style={styles.episodePlay}>▶</Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                )}
            </ScrollView>
        </SafeAreaView>
    );
}

// =================== DOWNLOAD / GET THE APP SCREEN ===================
function DownloadScreen({ navigation }) {
    const [detectedOS, setDetectedOS] = useState('web');
    useEffect(() => {
        const ua = (navigator.userAgent || '').toLowerCase();
        if (/android/.test(ua)) setDetectedOS('android');
        else if (/iphone|ipad|ipod/.test(ua)) setDetectedOS('ios');
        else if (/windows/.test(ua)) setDetectedOS('windows');
        else if (/mac os/.test(ua)) setDetectedOS('mac');
        else if (/linux/.test(ua)) setDetectedOS('linux');
    }, []);

    const DOWNLOAD_EXE_SIZE_MB = 35.9;

    const cards = [
        {
            id: 'web', os: 'Web', emoji: '🌐', title: 'Open in Browser', sub: 'Works everywhere — instant access.', cta: 'Open App', action: () => window.open('https://ls7m73ztxvfc2.space.minimax.io', '_blank'),
            primary: detectedOS === 'web', badge: 'Recommended'
        },
        {
            id: 'android', os: 'Android', emoji: '🤖', title: 'Android APK', sub: 'Install on phone, tablet, or Android TV. Sideload for now; Play Store later.', cta: 'Coming Soon — APK Build Guide', action: () => window.open('https://github.com/muhdfaisalwork-gif/streamapp/blob/main/packaging/android/BUILD_INSTRUCTIONS.md', '_blank'),
            primary: detectedOS === 'android', badge: 'Sideload ready'
        },
        {
            id: 'windows', os: 'Windows', emoji: '🪟', title: 'Windows Desktop', sub: 'StreamApp.exe — ${DOWNLOAD_EXE_SIZE_MB} MB native launcher. Opens the web app, adds itself to Windows Startup.', cta: '⬇ Download StreamApp.exe', action: () => window.open('https://github.com/muhdfaisalwork-gif/streamapp/releases/latest/download/StreamApp.exe', '_blank'),
            primary: detectedOS === 'windows', badge: '${DOWNLOAD_EXE_SIZE_MB} MB'
        },
        {
            id: 'mac', os: 'macOS', emoji: '🍎', title: 'macOS Desktop', sub: 'Launcher .pkg — native, signs itself, runs the web app in your default browser.', cta: '⬇ Download StreamApp.dmg', action: () => window.open('https://github.com/muhdfaisalwork-gif/streamapp/releases/latest/download/StreamApp.dmg', '_blank'),
            primary: detectedOS === 'mac', badge: 'Apple Silicon + Intel'
        },
        {
            id: 'linux', os: 'Linux', emoji: '🐧', title: 'Linux Desktop', sub: 'Debian + RPM + AppImage — works on Ubuntu, Fedora, Arch.', cta: '⬇ Download StreamApp.AppImage', action: () => window.open('https://github.com/muhdfaisalwork-gif/streamapp/releases/latest/download/StreamApp.AppImage', '_blank'),
            primary: detectedOS === 'linux', badge: 'All distros'
        },
        {
            id: 'ios', os: 'iOS / iPadOS', emoji: '📱', title: 'iPhone & iPad', sub: 'Add to Home Screen from Safari to install as a PWA. TestFlight build coming soon.', cta: 'Add to Home Screen', action: () => {
                const shareSheet = document.querySelector('meta[name="apple-mobile-web-app-capable"]') ? null : null;
                alert('To install on iPhone/iPad:\n\n1. Open https://ls7m73ztxvfc2.space.minimax.io in Safari\n2. Tap the Share button (up-arrow)\n3. Tap "Add to Home Screen"\n4. Confirm the name StreamApp and tap Add');
            },
            primary: detectedOS === 'ios', badge: 'PWA ready'
        }
    ];

    return (
        <SafeAreaView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.title}>📥 Get the App</Text>
                <Text style={styles.subtitle}>
                    Detected: {detectedOS.toUpperCase()} — primary option highlighted. All downloads live on GitHub Releases.
                </Text>
            </View>
            <ScrollView contentContainerStyle={{ paddingBottom: 40 }}>
                {cards.map(card => (
                    <TouchableOpacity
                        key={card.id}
                        onPress={card.action}
                        style={[styles.cardInfoCard, card.primary && { borderColor: COLORS.accent, borderWidth: 2 }]}
                        activeOpacity={0.8}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
                            <Text style={{ fontSize: 28, marginRight: 12 }}>{card.emoji}</Text>
                            <View style={{ flex: 1 }}>
                                <Text style={styles.cardTitle}>{card.title}</Text>
                                <Text style={styles.cardSub}>{card.os}</Text>
                            </View>
                            {card.badge && (
                                <View style={[styles.badge, card.primary && { backgroundColor: COLORS.accent }]}>
                                    <Text style={styles.badgeText}>{card.badge}</Text>
                                </View>
                            )}
                        </View>
                        <Text style={styles.cardDesc}>{card.sub}</Text>
                        <View style={[styles.cta, card.primary && { backgroundColor: COLORS.accent }]}>
                            <Text style={[styles.ctaText, card.primary && { color: '#0a0a0a', fontWeight: '800' }]}>{card.cta}</Text>
                        </View>
                    </TouchableOpacity>
                ))}
                <View style={{ marginTop: 20, padding: 16, backgroundColor: '#1a1a1a', borderRadius: 12 }}>
                    <Text style={{ color: '#fbbf24', fontWeight: '700', marginBottom: 6 }}>⚡ Pro Tip — PWA Install</Text>
                    <Text style={{ color: '#d4d4d4', lineHeight: 20 }}>
                        Every modern browser (Chrome, Edge, Safari, Firefox) supports one-click install.
                        Look for the "Install" icon in the address bar — adds StreamApp to your home screen or app menu
                        without any download.
                    </Text>
                </View>
            </ScrollView>
        </SafeAreaView>
    );
}

// =================== NAVIGATION ===================
const Stack = createNativeStackNavigator();

function HomeStack({ route }) {
    return (
        <Stack.Navigator screenOptions={{
            headerStyle: { backgroundColor: COLORS.surface },
            headerTintColor: COLORS.textPrimary,
            contentStyle: { backgroundColor: COLORS.bg }
        }}>
            <Stack.Screen name="HomeMain" component={HomeScreen} initialParams={route?.params} options={{ headerShown: false }} />
            <Stack.Screen name="Player" component={PlayerScreen} options={{ title: 'Now Playing' }} />
            <Stack.Screen name="TVDetail" component={TVDetailScreen} options={{ title: 'TV Series' }} />
        </Stack.Navigator>
    );
}

function SearchStack({ route }) {
    return (
        <Stack.Navigator screenOptions={{
            headerStyle: { backgroundColor: COLORS.surface },
            headerTintColor: COLORS.textPrimary,
            contentStyle: { backgroundColor: COLORS.bg }
        }}>
            <Stack.Screen name="SearchMain" component={SearchScreen} initialParams={route?.params} options={{ headerShown: false }} />
            <Stack.Screen name="Player" component={PlayerScreen} options={{ title: 'Now Playing' }} />
            <Stack.Screen name="TVDetail" component={TVDetailScreen} options={{ title: 'TV Series' }} />
        </Stack.Navigator>
    );
}

function WatchlistStack({ route }) {
    return (
        <Stack.Navigator screenOptions={{
            headerStyle: { backgroundColor: COLORS.surface },
            headerTintColor: COLORS.textPrimary,
            contentStyle: { backgroundColor: COLORS.bg }
        }}>
            <Stack.Screen name="WatchlistMain" component={WatchlistScreen} initialParams={route?.params} options={{ headerShown: false }} />
            <Stack.Screen name="Player" component={PlayerScreen} options={{ title: 'Now Playing' }} />
            <Stack.Screen name="TVDetail" component={TVDetailScreen} options={{ title: 'TV Series' }} />
        </Stack.Navigator>
    );
}

function CountryStack({ route }) {
    return (
        <Stack.Navigator screenOptions={{
            headerStyle: { backgroundColor: COLORS.surface },
            headerTintColor: COLORS.textPrimary,
            contentStyle: { backgroundColor: COLORS.bg }
        }}>
            <Stack.Screen name="CountryMain" component={CountryScreen} initialParams={route?.params} options={{ headerShown: false }} />
            <Stack.Screen name="Player" component={PlayerScreen} options={{ title: 'Now Playing' }} />
            <Stack.Screen name="TVDetail" component={TVDetailScreen} options={{ title: 'TV Series' }} />
        </Stack.Navigator>
    );
}

function GenreStack({ route }) {
    return (
        <Stack.Navigator screenOptions={{
            headerStyle: { backgroundColor: COLORS.surface },
            headerTintColor: COLORS.textPrimary,
            contentStyle: { backgroundColor: COLORS.bg }
        }}>
            <Stack.Screen name="GenreMain" component={GenreScreen} initialParams={route?.params} options={{ headerShown: false }} />
            <Stack.Screen name="Player" component={PlayerScreen} options={{ title: 'Now Playing' }} />
        </Stack.Navigator>
    );
}

function DownloadStack({ route }) {
    return (
        <Stack.Navigator screenOptions={{
            headerStyle: { backgroundColor: COLORS.surface },
            headerTintColor: COLORS.textPrimary,
            contentStyle: { backgroundColor: COLORS.bg }
        }}>
            <Stack.Screen name="DownloadMain" component={DownloadScreen} initialParams={route?.params} options={{ headerShown: false }} />
        </Stack.Navigator>
    );
}

const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();

function TabIcon({ emoji, focused }) {
    return <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.5 }}>{emoji}</Text>;
}

// =================== CUSTOM SIDEBAR (with country selector + no-ads indicator) ===================
function CustomDrawerContent({ navigation, state }) {
    const [countries, setCountries] = useState([]);
    const [languages, setLanguages] = useState([]);
    const [liveStatus, setLiveStatus] = useState({ liveAvailable: false, liveTitlesCached: 0, totalUniqueTitles: 0, curatedTitles: 0 });
    const activeRoute = state.routeNames[state.index];

    const onNav = (route, params) => {
        if (route === 'Countries') {
            navigation.navigate('Countries', { screen: 'CountryMain', params: params || { countryKey: 'all' } });
        } else if (route === 'Genres') {
            navigation.navigate('Genres', { screen: 'GenreMain', params: params || { genre: 'Action' } });
        } else if (route === 'Search') {
            navigation.navigate('Search', { screen: 'SearchMain', params });
        } else if (route === 'Home') {
            navigation.navigate('Home', { screen: 'HomeMain', params });
        } else if (route === 'Watchlist') {
            navigation.navigate('Watchlist', { screen: 'WatchlistMain', params });
        } else if (route === 'Download') {
            navigation.navigate('Download', { screen: 'DownloadMain', params });
        } else {
            navigation.navigate(route, params);
        }
        try { navigation.closeDrawer(); } catch (e) {}
    };

    useEffect(() => {
        fetch(`${API_BASE}/countries`).then(r => r.json()).then(j => setCountries(j.countries || [])).catch(e => console.error(e));
        fetch(`${API_BASE}/languages`).then(r => r.json()).then(j => setLanguages(j.languages || [])).catch(e => console.error(e));

        const checkLive = () => {
            fetch(`${API_BASE}/health`)
                .then(r => r.json())
                .then(j => {
                    const liveUp = j.liveAvailable === true;
                    // When live is DOWN, force liveTitlesCached=0 and curatedTitles=totalUniqueTitles
                    // so the status pill doesn't lie about cached live titles.
                    // When live comes back UP, the next /health fetch will populate liveTitlesCached.
                    setLiveStatus({
                        liveAvailable: liveUp,
                        liveTitlesCached: liveUp ? (j.liveTitlesCached || 0) : 0,
                        totalUniqueTitles: j.totalUniqueTitles || 0,
                        curatedTitles: liveUp
                            ? Math.max(0, (j.totalUniqueTitles || 0) - (j.liveTitlesCached || 0))
                            : (j.totalUniqueTitles || 0)
                    });
                })
                .catch(() => setLiveStatus({ liveAvailable: false, liveTitlesCached: 0, totalUniqueTitles: 0, curatedTitles: 0 }));
        };
        checkLive();
        const t = setInterval(checkLive, 10000);
        return () => clearInterval(t);
    }, []);

    const items = [
        { key: 'Home', emoji: '🏠', label: 'Home' },
        { key: 'Search', emoji: '🔍', label: 'Search' },
        { key: 'Genres', emoji: '🎭', label: 'All Genres' },
        { key: 'Countries', emoji: '🌍', label: 'All Countries' },
        { key: 'Watchlist', emoji: '📺', label: 'Watchlist' },
        { key: 'Download', emoji: '📥', label: 'Get the App' },
        { key: 'Settings', emoji: '⚙️', label: 'Settings' }
    ];

    const popularGenres = [
        { label: 'Action', emoji: '💥' },
        { label: 'Comedy', emoji: '😂' },
        { label: 'Sci-Fi', emoji: '🚀' },
        { label: 'Horror', emoji: '👻' },
        { label: 'Drama', emoji: '🎭' },
        { label: 'Animation', emoji: '🎨' },
        { label: 'Romance', emoji: '💕' },
        { label: 'Thriller', emoji: '🔪' },
        { label: 'Documentary', emoji: '📹' },
        { label: 'Crime', emoji: '🕵️' },
        { label: 'Fantasy', emoji: '🧙' },
        { label: 'Family', emoji: '👨‍👩‍👧' }
    ];

    const SIDEBAR_WIDTH = 260;

    return (
        <SafeAreaView style={{ width: SIDEBAR_WIDTH, backgroundColor: COLORS.surface, flex: 1 }}>
            {/* Brand header */}
            <View style={styles.drawerHeader}>
                <View style={styles.drawerLogo}>
                    <Text style={styles.drawerLogoIcon}>🎬</Text>
                </View>
                <View style={{ flex: 1 }}>
                    <Text style={styles.drawerBrand}>StreamApp</Text>
                    <Text style={styles.drawerSub}>Movies & TV, free</Text>
                </View>
            </View>

            {/* No-ads badge */}
            <View style={styles.noAdsBadge}>
                <View style={styles.noAdsIcon}><Text style={styles.noAdsIconText}>✓</Text></View>
                <Text style={styles.noAdsText}>100% Ad-Free • No Trackers</Text>
            </View>

            {/* Live status badge — honest state, no stale number */}
            <View style={[styles.liveBadge, { borderColor: liveStatus.liveAvailable ? COLORS.success : '#EF4444' }]}>
                <Text style={{ fontSize: 9, color: liveStatus.liveAvailable ? COLORS.success : '#EF4444', marginRight: 6 }}>●</Text>
                <Text style={[styles.liveBadgeText, { color: liveStatus.liveAvailable ? COLORS.success : '#EF4444' }]}>
                    {liveStatus.liveAvailable
                        ? `Live: ${liveStatus.liveTitlesCached.toLocaleString()} ✓`
                        : `Live: offline (curated: ${liveStatus.curatedTitles.toLocaleString()})`}
                </Text>
            </View>

            {/* Main nav */}
            <ScrollView style={{ flex: 1 }}>
                {items.map(item => {
                    const focused = activeRoute === item.key;
                    return (
                        <TouchableOpacity
                            key={item.key}
                            style={[styles.drawerItem, focused && styles.drawerItemActive]}
                            onPress={() => {
                                if (item.key === 'Countries') onNav('Countries', { countryKey: 'all' });
                                else if (item.key === 'Genres') onNav('Genres', { genre: 'Action' });
                                else onNav(item.key);
                            }}
                        >
                            <Text style={styles.drawerEmoji}>{item.emoji}</Text>
                            <Text style={[styles.drawerLabel, focused && styles.drawerLabelActive]}>{item.label}</Text>
                        </TouchableOpacity>
                    );
                })}

                {/* Genres section */}
                <View style={styles.drawerSection}>
                    <Text style={styles.drawerSectionTitle}>🎭 Browse by Genre</Text>
                </View>
                <View style={styles.drawerGenreGrid}>
                    {popularGenres.map(g => (
                        <TouchableOpacity
                            key={g.label}
                            style={styles.drawerGenreChip}
                            onPress={() => onNav('Genres', { genre: g.label })}
                        >
                            <Text style={styles.drawerGenreEmoji}>{g.emoji}</Text>
                            <Text style={styles.drawerGenreText}>{g.label}</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Countries section */}
                <View style={styles.drawerSection}>
                    <Text style={styles.drawerSectionTitle}>🌍 By Country / Region ({countries.length - 1})</Text>
                </View>
                {countries.filter(c => c.key !== 'all').map(c => (
                    <TouchableOpacity
                        key={c.key}
                        style={styles.drawerCountryItem}
                        onPress={() => onNav('Countries', { countryKey: c.key })}
                    >
                        <Text style={styles.drawerCountryFlag}>{c.flag}</Text>
                        <Text style={styles.drawerCountryLabel} numberOfLines={1}>{c.label}</Text>
                        <Text style={styles.drawerCountryCount}>{c.count}</Text>
                    </TouchableOpacity>
                ))}

                {/* Languages section */}
                <View style={styles.drawerSection}>
                    <Text style={styles.drawerSectionTitle}>🗣️ Languages ({languages.length})</Text>
                </View>
                <View style={styles.langGrid}>
                    {languages.map(l => (
                        <TouchableOpacity
                            key={l.code}
                            style={styles.langChip}
                            onPress={() => onNav('Search', { prefLang: l.code })}
                        >
                            <Text style={styles.langFlag}>{l.flag}</Text>
                            <Text style={styles.langCode}>{l.code.toUpperCase()}</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Sources section */}
                <View style={styles.drawerSection}>
                    <Text style={styles.drawerSectionTitle}>📡 All 10 Sources</Text>
                </View>
                <View style={styles.sourcesList}>
                    {['BeeTV','MovieBoxHD','OnStream','HDO Box','123movies','YTS','YIFY','tmovies','donkey.to','uflix'].map(s => (
                        <TouchableOpacity
                            key={s}
                            style={styles.sourcePill}
                            onPress={() => onNav('Search', { prefLang: s })}
                        >
                            <Text style={styles.sourcePillDot}>●</Text>
                            <Text style={styles.sourcePillText}>{s}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </ScrollView>

            {/* Footer */}
            <View style={styles.drawerFooter}>
                <Text style={styles.drawerFooterText}>v2.0.0 • build 20260921 • 100k+ titles live</Text>
                <Text style={styles.drawerFooterSub}>10 live sources • 22 countries • 20 languages</Text>
            </View>
        </SafeAreaView>
    );
}

export default function App() {
    const { width } = useWindowDimensions();
    const isLargeScreen = width >= 768;

    const drawerOptions = {
        headerStyle: { backgroundColor: COLORS.surface },
        headerTintColor: COLORS.textPrimary,
        sceneStyle: { backgroundColor: COLORS.bg },
        drawerActiveTintColor: COLORS.brand,
        drawerInactiveTintColor: COLORS.textPrimary,
        drawerStyle: { backgroundColor: COLORS.surface, borderRightColor: COLORS.border },
        drawerType: isLargeScreen ? 'permanent' : 'front',
        drawerContent: (props) => <CustomDrawerContent {...props} />
    };

    return (
        <NavigationContainer>
            <Drawer.Navigator
                initialRouteName="Home"
                screenOptions={{
                    ...drawerOptions,
                    headerShown: false
                }}
                drawerContent={(props) => <CustomDrawerContent {...props} />}
            >
                <Drawer.Screen name="Home" component={HomeStack} />
                <Drawer.Screen name="Search" component={SearchStack} />
                <Drawer.Screen name="Genres" component={GenreStack} />
                <Drawer.Screen name="Countries" component={CountryStack} />
                <Drawer.Screen name="Watchlist" component={WatchlistStack} />
                <Drawer.Screen name="Download" component={DownloadStack} />
                <Drawer.Screen name="Settings" component={SettingsScreen} />
            </Drawer.Navigator>
        </NavigationContainer>
    );
}

// =================== STYLES ===================
const styles = StyleSheet.create({
    screen: { flex: 1, backgroundColor: COLORS.bg },
    sectionHeader: {
        paddingHorizontal: 16, paddingVertical: 12,
        flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'
    },
    sectionTitle: { color: COLORS.textPrimary, fontSize: 20, fontWeight: '700' },
    clearText: { color: COLORS.brand, fontSize: 13 },

    heroBanner: {
        height: 460, marginBottom: 16, position: 'relative', justifyContent: 'flex-end'
    },
    heroOverlay: {
        padding: 20, paddingTop: 60, backgroundColor: 'rgba(0,0,0,0)'
    },
    heroBadge: {
        backgroundColor: COLORS.brand, alignSelf: 'flex-start',
        paddingHorizontal: 8, paddingVertical: 3, borderRadius: 3, marginBottom: 8
    },
    heroBadgeText: { color: '#fff', fontSize: 10, fontWeight: '800', letterSpacing: 0.5 },
    heroTitle: { color: COLORS.textPrimary, fontSize: 32, fontWeight: '800', letterSpacing: -0.5 },
    heroMeta: { color: COLORS.textSecondary, fontSize: 13, marginTop: 6 },
    heroDescription: { color: COLORS.textSecondary, fontSize: 13, lineHeight: 18, marginTop: 8 },
    heroActions: { flexDirection: 'row', marginTop: 16, gap: 10 },
    heroPlayButton: {
        backgroundColor: COLORS.brand, flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: 20, paddingVertical: 10, borderRadius: 6
    },
    heroPlayIcon: { color: '#fff', fontSize: 14, marginRight: 6 },
    heroPlayText: { color: '#fff', fontSize: 14, fontWeight: '700' },
    heroWatchlistButton: {
        backgroundColor: 'rgba(255,255,255,0.15)', flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: 16, paddingVertical: 10, borderRadius: 6
    },
    heroWatchlistIcon: { color: '#fff', fontSize: 16, marginRight: 6, fontWeight: '700' },
    heroWatchlistText: { color: '#fff', fontSize: 13, fontWeight: '600' },
    heroIndicators: {
        position: 'absolute', bottom: 12, left: 0, right: 0,
        flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6
    },
    heroDot: {
        width: 6, height: 6, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.4)', marginHorizontal: 3
    },
    heroDotActive: { backgroundColor: COLORS.brand, width: 18 },

    continueWatchingSection: { marginBottom: 16 },
    continueWatchingList: { paddingHorizontal: 12, paddingRight: 16 },
    continueWatchingEmpty: { paddingHorizontal: 16, paddingVertical: 8, color: COLORS.textMuted, fontSize: 13 },

    categorySection: { marginVertical: 12 },
    categoryHeader: {
        paddingHorizontal: 16, paddingBottom: 8,
        flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline'
    },
    categoryTitle: { color: COLORS.textPrimary, fontSize: 18, fontWeight: '700' },
    categoryMeta: { color: COLORS.textMuted, fontSize: 12 },
    categoryList: { paddingHorizontal: 12, paddingRight: 16 },

    card: {
        width: 140, minWidth: 140, maxWidth: 140, flex: 0, flexShrink: 0,
        marginHorizontal: 4, marginVertical: 6,
        backgroundColor: COLORS.surface, borderRadius: 6, overflow: 'hidden'
    },
    cardSlot: {
        width: 148, minWidth: 148, maxWidth: 148, flex: 0, flexShrink: 0
    },
    cardSlotMore: {
        width: 132, minWidth: 132, maxWidth: 132,
    },
    cardSlotMorePoster: {
        backgroundColor: COLORS.surface,
        borderWidth: 1, borderColor: COLORS.border,
        borderStyle: 'dashed',
    },
    cardSlotMoreText: { color: COLORS.textPrimary, fontSize: 14, fontWeight: '700', marginBottom: 4 },
    cardSlotMoreCount: { color: COLORS.brand, fontSize: 12, fontWeight: '600' },
    cardLarge: { width: 180, minWidth: 180, maxWidth: 180, flex: 0, flexShrink: 0 },
    cardPoster: { width: '100%', aspectRatio: 2/3, backgroundColor: COLORS.surfaceAlt, overflow: 'hidden' },
    cardInfo: { padding: 8 },
    cardTitle: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '600' },
    cardMeta: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
    cardSub: { color: COLORS.textMuted, fontSize: 11, fontWeight: '500', textTransform: 'uppercase', letterSpacing: 0.5 },
    cardDesc: { color: COLORS.textSecondary, fontSize: 13, lineHeight: 19, marginTop: 8 },
    cardInfoCard: {
        backgroundColor: COLORS.surface,
        marginHorizontal: 16, marginVertical: 6,
        padding: 16, borderRadius: 12,
        borderWidth: 1, borderColor: COLORS.border
    },
    cta: {
        marginTop: 12, alignSelf: 'flex-start',
        backgroundColor: COLORS.surfaceAlt,
        paddingHorizontal: 16, paddingVertical: 10,
        borderRadius: 8
    },
    ctaText: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '700' },
    badge: {
        position: 'absolute', top: 6, right: 6,
        backgroundColor: 'rgba(0,0,0,0.7)', paddingHorizontal: 5, paddingVertical: 2, borderRadius: 3
    },
    badgeText: { color: '#fff', fontSize: 9, fontWeight: '700' },
    progressBarBg: {
        position: 'absolute', bottom: 50, left: 0, right: 0, height: 3,
        backgroundColor: 'rgba(0,0,0,0.6)'
    },
    progressBarFill: { height: '100%', backgroundColor: COLORS.brand },

    searchBar: {
        flexDirection: 'row', alignItems: 'center',
        backgroundColor: COLORS.surface, margin: 16,
        paddingHorizontal: 14, borderRadius: 10, borderWidth: 1, borderColor: COLORS.border
    },
    searchIcon: { fontSize: 16, marginRight: 8 },
    searchInput: { flex: 1, color: COLORS.textPrimary, fontSize: 15, paddingVertical: 12 },
    clearButton: { color: COLORS.textMuted, fontSize: 16, paddingHorizontal: 8 },

    filterRow: {
        flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, marginBottom: 12, gap: 8
    },
    filterChip: {
        paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16,
        backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border
    },
    filterChipActive: { backgroundColor: COLORS.brand, borderColor: COLORS.brand },
    filterChipText: { color: COLORS.textSecondary, fontSize: 12, fontWeight: '600' },
    filterChipTextActive: { color: '#fff' },
    resultCount: { color: COLORS.textMuted, fontSize: 11, marginLeft: 'auto' },

    searchGrid: { paddingHorizontal: 8, paddingBottom: 24 },
    searchRow: { justifyContent: 'flex-start' },

    emptyState: { paddingVertical: 80, alignItems: 'center', paddingHorizontal: 24 },
    emptyIcon: { fontSize: 48, marginBottom: 12 },
    emptyTitle: { color: COLORS.textPrimary, fontSize: 18, fontWeight: '700' },
    emptySubtitle: { color: COLORS.textSecondary, fontSize: 14, marginTop: 4, textAlign: 'center' },

    skeletonGrid: { flexDirection: 'row', flexWrap: 'wrap', padding: 12, gap: 12 },
    skeletonCard: { width: '30%', borderRadius: 6, padding: 8, marginBottom: 12 },
    skeletonPoster: { width: '100%', aspectRatio: 2/3, borderRadius: 4, marginBottom: 8 },
    skeletonLine: { height: 10, borderRadius: 2, marginBottom: 6 },

    posterFallback: {
        backgroundColor: COLORS.surfaceAlt, justifyContent: 'center',
        alignItems: 'center', padding: 8
    },
    posterFallbackIcon: { fontSize: 28, marginBottom: 4 },
    posterFallbackText: { color: COLORS.textSecondary, fontSize: 10, textAlign: 'center' },
    posterImage: { width: '100%', height: '100%' },
    posterTopLeft: { position: 'absolute', left: 6 },
    posterTopRight: { position: 'absolute', top: 6, right: 6, maxWidth: '60%' },
    posterBottomLeft: { position: 'absolute', bottom: 6, left: 6 },
    qualityBadge: { paddingHorizontal: 5, paddingVertical: 2, borderRadius: 3 },
    qualityBadgeGold: { backgroundColor: '#f5c518' },
    qualityBadgeCyan: { backgroundColor: '#00bcd4' },
    qualityBadgeMuted: { backgroundColor: 'rgba(255,255,255,0.6)' },
    qualityBadgeText: { color: '#000', fontSize: 9, fontWeight: '900', letterSpacing: 0.5 },
    sourceBadge: { backgroundColor: 'rgba(0,0,0,0.75)', paddingHorizontal: 5, paddingVertical: 2, borderRadius: 3 },
    sourceBadgeText: { color: '#fff', fontSize: 8, fontWeight: '700' },
    subtitleBadge: { backgroundColor: 'rgba(255,255,255,0.85)', paddingHorizontal: 4, paddingVertical: 1, borderRadius: 2 },
    subtitleBadgeText: { color: '#000', fontSize: 8, fontWeight: '900', letterSpacing: 0.5 },
    viewCountBadge: { backgroundColor: 'rgba(0,0,0,0.65)', paddingHorizontal: 5, paddingVertical: 2, borderRadius: 3 },
    viewCountText: { color: '#fff', fontSize: 9, fontWeight: '700' },

    playerWrapper: { width: '100%', aspectRatio: 16 / 9, maxHeight: 720, minHeight: 240, backgroundColor: '#000' },
    iframeFallback: { flex: 1, position: 'relative', justifyContent: 'center', alignItems: 'center' },
    iframeFallbackOverlay: { padding: 20 },
    iframeFallbackText: { color: COLORS.textSecondary, fontSize: 14, textAlign: 'center' },

    playerLoadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 40 },
    loadingText: { color: COLORS.textPrimary, marginTop: 16, fontSize: 14 },
    loadingSubtext: { color: COLORS.textSecondary, marginTop: 4, fontSize: 12 },

    playerDetails: { flex: 1 },
    playerDetailsContent: { padding: 16 },
    playerHeader: {
        flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12
    },
    playerTitle: { color: COLORS.textPrimary, fontSize: 22, fontWeight: '800' },
    playerSubtitle: { color: COLORS.textSecondary, fontSize: 13, marginTop: 4 },
    watchlistBtn: {
        paddingHorizontal: 14, paddingVertical: 8, borderRadius: 6,
        borderWidth: 1, borderColor: COLORS.border, marginLeft: 12
    },
    watchlistBtnText: { color: COLORS.textPrimary, fontSize: 12, fontWeight: '600' },
    watchlistBtnActive: { color: COLORS.brand, borderColor: COLORS.brand },

    description: { color: COLORS.textSecondary, fontSize: 13, lineHeight: 20, marginVertical: 12 },
    metaGrid: { gap: 8, marginBottom: 16 },
    metaItem: { paddingVertical: 8, borderTopWidth: 1, borderTopColor: COLORS.border },
    metaLabel: { color: COLORS.textMuted, fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 },
    metaValue: { color: COLORS.textPrimary, fontSize: 13 },

    sourcesCard: {
        backgroundColor: COLORS.surface, borderRadius: 10, padding: 14, marginBottom: 16
    },
    sourcesTitle: { color: COLORS.textPrimary, fontSize: 14, fontWeight: '700', marginBottom: 4 },
    sourcesSubtitle: { color: COLORS.textMuted, fontSize: 11, marginBottom: 12 },
    sourceRow: {
        flexDirection: 'row', alignItems: 'center',
        padding: 12, marginVertical: 3, backgroundColor: COLORS.surfaceAlt, borderRadius: 6
    },
    sourceRowActive: { borderColor: COLORS.accent, borderWidth: 1, backgroundColor: '#1a2333' },
    sourceLabel: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '600' },
    sourceMeta: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
    sourceCheck: { color: COLORS.accent, fontSize: 13, fontWeight: '700', marginLeft: 8 },
    switchMirrorContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#141414',
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderBottomWidth: 1,
        borderBottomColor: COLORS.border,
        gap: 8,
    },
    switchMirrorBanner: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#222',
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 6,
    },
    switchMirrorText: {
        color: COLORS.accent,
        fontSize: 12,
        fontWeight: '600',
    },
    openExternalTabBtn: {
        backgroundColor: 'rgba(255, 255, 255, 0.12)',
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.2)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    openExternalTabText: {
        color: COLORS.textPrimary,
        fontSize: 12,
        fontWeight: '600',
    },

    errorState: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
    errorIcon: { fontSize: 48, marginBottom: 12 },
    errorTitle: { color: COLORS.textPrimary, fontSize: 20, fontWeight: '700' },
    errorMessage: { color: COLORS.textSecondary, fontSize: 14, textAlign: 'center', marginTop: 8 },
    retryButton: {
        backgroundColor: COLORS.brand, paddingVertical: 12, paddingHorizontal: 28,
        borderRadius: 6, marginTop: 20
    },
    retryButtonText: { color: '#fff', fontWeight: '700', fontSize: 14 },
    backButton: {
        paddingVertical: 12, paddingHorizontal: 24, borderRadius: 6,
        backgroundColor: COLORS.surface, alignSelf: 'center',
        marginTop: 12, borderWidth: 1, borderColor: COLORS.border
    },
    backButtonText: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '600' },

    tvHeader: { height: 320, position: 'relative', justifyContent: 'flex-end' },
    tvHeaderPoster: { ...StyleSheet.absoluteFillObject },
    tvHeaderOverlay: { padding: 20, backgroundColor: 'rgba(0,0,0,0.6)' },

    seasonSelector: { paddingHorizontal: 16, paddingVertical: 12 },
    seasonChip: {
        paddingHorizontal: 14, paddingVertical: 8, borderRadius: 6,
        backgroundColor: COLORS.surface, marginRight: 8, borderWidth: 1, borderColor: COLORS.border
    },
    seasonChipActive: { backgroundColor: COLORS.brand, borderColor: COLORS.brand },
    seasonChipText: { color: COLORS.textSecondary, fontSize: 13, fontWeight: '600' },
    seasonChipTextActive: { color: '#fff' },

    episodesList: { padding: 16, gap: 8 },
    episodeRow: {
        flexDirection: 'row', alignItems: 'center',
        backgroundColor: COLORS.surface, padding: 12, borderRadius: 8,
        marginBottom: 6
    },
    episodeNumber: {
        width: 36, height: 36, borderRadius: 18,
        backgroundColor: COLORS.brand, justifyContent: 'center',
        alignItems: 'center', marginRight: 12
    },
    episodeNumberText: { color: '#fff', fontSize: 14, fontWeight: '800' },
    episodeTitle: { color: COLORS.textPrimary, fontSize: 14, fontWeight: '600' },
    episodeMeta: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },
    episodePlay: { color: COLORS.accent, fontSize: 18, marginLeft: 8 },

    settingsContent: { padding: 20 },
    settingsTitle: { color: COLORS.textPrimary, fontSize: 28, fontWeight: '800', marginBottom: 16 },
    settingsCard: { backgroundColor: COLORS.surface, borderRadius: 10, padding: 16, marginBottom: 12 },
    settingsCardTitle: { color: COLORS.textPrimary, fontSize: 15, fontWeight: '700', marginBottom: 4 },
    settingsCardSubtitle: { color: COLORS.textMuted, fontSize: 12, marginBottom: 12 },
    settingsCardBody: { color: COLORS.textSecondary, fontSize: 13, lineHeight: 20 },
    sourceChips: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
    sourceChip: {
        paddingHorizontal: 14, paddingVertical: 8, borderRadius: 16,
        backgroundColor: COLORS.surfaceAlt, borderWidth: 1, borderColor: COLORS.border
    },
    sourceChipActive: { backgroundColor: COLORS.accent, borderColor: COLORS.accent },
    sourceChipText: { color: COLORS.textSecondary, fontSize: 12, fontWeight: '600' },
    sourceChipTextActive: { color: '#000' },

    settingRow: {
        flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8
    },
    settingLabel: { color: COLORS.textPrimary, fontSize: 13 },
    toggle: {
        width: 44, height: 24, borderRadius: 12,
        backgroundColor: COLORS.border, padding: 2, justifyContent: 'center'
    },
    toggleOn: { backgroundColor: COLORS.brand },
    toggleKnob: { width: 20, height: 20, borderRadius: 10, backgroundColor: '#fff' },
    toggleKnobOn: { transform: [{ translateX: 20 }] },

    statRow: {
        flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6
    },
    statLabel: { color: COLORS.textSecondary, fontSize: 13 },
    statValue: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '700' },

    dangerButton: {
        marginTop: 12, paddingVertical: 10, paddingHorizontal: 14,
        borderRadius: 6, borderWidth: 1, borderColor: COLORS.brand
    },
    dangerButtonText: { color: COLORS.brand, fontSize: 13, fontWeight: '600', textAlign: 'center' },

    // ===== SIDEBAR =====
    drawerHeader: {
        flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: 16, paddingVertical: 18,
        borderBottomWidth: 1, borderBottomColor: COLORS.border
    },
    drawerLogo: {
        width: 40, height: 40, borderRadius: 20,
        backgroundColor: COLORS.brand, justifyContent: 'center',
        alignItems: 'center', marginRight: 12
    },
    drawerLogoIcon: { fontSize: 20 },
    drawerBrand: { color: COLORS.textPrimary, fontSize: 17, fontWeight: '800' },
    drawerSub: { color: COLORS.textMuted, fontSize: 11, marginTop: 2 },

    noAdsBadge: {
        flexDirection: 'row', alignItems: 'center',
        backgroundColor: 'rgba(16,185,129,0.12)',
        marginHorizontal: 12, marginTop: 12, marginBottom: 4,
        paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8,
        borderWidth: 1, borderColor: COLORS.success
    },
    noAdsIcon: {
        width: 20, height: 20, borderRadius: 10,
        backgroundColor: COLORS.success, marginRight: 8,
        justifyContent: 'center', alignItems: 'center'
    },
    noAdsIconText: { color: '#000', fontSize: 12, fontWeight: '900', lineHeight: 14 },
    noAdsText: { color: COLORS.success, fontSize: 12, fontWeight: '700' },

    drawerItem: {
        flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: 16, paddingVertical: 12
    },
    drawerItemActive: {
        backgroundColor: 'rgba(229,9,20,0.15)',
        borderLeftWidth: 3, borderLeftColor: COLORS.brand
    },
    drawerEmoji: { fontSize: 18, marginRight: 12 },
    drawerLabel: { color: COLORS.textSecondary, fontSize: 14, fontWeight: '600' },
    drawerLabelActive: { color: COLORS.brand, fontWeight: '700' },

    drawerSection: {
        paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8,
        borderTopWidth: 1, borderTopColor: COLORS.border, marginTop: 8
    },
    drawerSectionTitle: {
        color: COLORS.textMuted, fontSize: 11, fontWeight: '700',
        letterSpacing: 1, textTransform: 'uppercase'
    },
    drawerCountryItem: {
        flexDirection: 'row', alignItems: 'center',
        paddingHorizontal: 16, paddingVertical: 8
    },
    drawerCountryFlag: { fontSize: 16, marginRight: 10 },
    drawerCountryLabel: { color: COLORS.textSecondary, fontSize: 13, flex: 1 },
    drawerCountryCount: {
        color: COLORS.textMuted, fontSize: 11, fontWeight: '600',
        backgroundColor: COLORS.surfaceAlt, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 8
    },

    drawerFooter: {
        padding: 16, borderTopWidth: 1, borderTopColor: COLORS.border
    },
    drawerFooterText: { color: COLORS.textMuted, fontSize: 11, fontWeight: '600' },
    drawerFooterSub: { color: COLORS.textMuted, fontSize: 10, marginTop: 3 },

    // ===== BROWSE BY COUNTRY / GENRE =====
    countryBar: {
        paddingHorizontal: 12, paddingVertical: 12, gap: 8
    },
    countryChip: {
        flexDirection: 'row', alignItems: 'center',
        backgroundColor: COLORS.surface, borderWidth: 1, borderColor: COLORS.border,
        paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, marginRight: 8
    },
    countryChipActive: { backgroundColor: COLORS.brand, borderColor: COLORS.brand },
    countryFlag: { fontSize: 16, marginRight: 6 },
    countryFlagActive: { fontSize: 16 },
    countryLabel: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '600' },
    countryLabelActive: { color: '#fff' },
    countryCount: {
        color: COLORS.textMuted, fontSize: 10, marginLeft: 6,
        fontWeight: '700', backgroundColor: COLORS.surfaceAlt,
        paddingHorizontal: 5, paddingVertical: 1, borderRadius: 6
    },
    countryCountActive: { color: '#fff', backgroundColor: 'rgba(0,0,0,0.25)' },

    browseHeader: { paddingHorizontal: 16, paddingBottom: 12 },
    browseTitle: { color: COLORS.textPrimary, fontSize: 22, fontWeight: '800' },
    browseSubtitle: { color: COLORS.textMuted, fontSize: 12, marginTop: 2 },

    // ===== LANGUAGE GRID =====
    langGrid: {
        flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12, gap: 6
    },
    langChip: {
        flexDirection: 'row', alignItems: 'center',
        backgroundColor: COLORS.surfaceAlt, paddingHorizontal: 8, paddingVertical: 4,
        borderRadius: 6, margin: 2
    },
    langFlag: { fontSize: 12, marginRight: 4 },
    langCode: { color: COLORS.textSecondary, fontSize: 10, fontWeight: '700' },

    // ===== SOURCES LIST =====
    sourcesList: { paddingHorizontal: 12, gap: 4 },
    sourcePill: {
        flexDirection: 'row', alignItems: 'center',
        backgroundColor: COLORS.surfaceAlt, paddingHorizontal: 10, paddingVertical: 6,
        borderRadius: 6, marginBottom: 3
    },
    sourcePillDot: { color: COLORS.success, fontSize: 8, marginRight: 8 },
    sourcePillText: { color: COLORS.textPrimary, fontSize: 12, fontWeight: '600' },

    // ===== LIVE MODE & STATUS STYLES =====
    searchModeRow: {
        flexDirection: 'row',
        paddingHorizontal: 16,
        paddingTop: 12,
        paddingBottom: 4,
        gap: 8
    },
    searchModeTab: {
        flex: 1,
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 8,
        backgroundColor: COLORS.surface,
        borderWidth: 1,
        borderColor: COLORS.border,
        alignItems: 'center',
        justifyContent: 'center'
    },
    searchModeTabActive: {
        backgroundColor: COLORS.surfaceAlt,
        borderColor: COLORS.brand
    },
    searchModeText: {
        color: COLORS.textMuted,
        fontSize: 12,
        fontWeight: '700'
    },
    searchModeTextActive: {
        color: COLORS.textPrimary
    },
    liveProgressBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: COLORS.surface,
        padding: 10,
        borderRadius: 8,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    liveProgressText: {
        color: COLORS.textSecondary,
        fontSize: 12,
        fontWeight: '600'
    },
    liveBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'rgba(255,255,255,0.04)',
        marginHorizontal: 12,
        marginTop: 6,
        marginBottom: 8,
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: 6,
        borderWidth: 1
    },
    liveBadgeText: {
        fontSize: 11,
        fontWeight: '700'
    },

    // AppHeader styles
    appHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: COLORS.surface,
        borderBottomWidth: 1,
        borderBottomColor: COLORS.border,
        zIndex: 10
    },
    appHeaderLeft: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    hamburgerButton: {
        marginRight: 14,
        padding: 4
    },
    hamburgerIcon: {
        color: COLORS.textPrimary,
        fontSize: 22,
        fontWeight: '700'
    },
    appHeaderBrandTouch: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    appHeaderLogo: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: COLORS.brand,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 8
    },
    appHeaderLogoIcon: {
        fontSize: 16
    },
    appHeaderBrand: {
        color: COLORS.textPrimary,
        fontSize: 18,
        fontWeight: '800',
        letterSpacing: -0.5
    },
    appHeaderTag: {
        marginLeft: 10,
        paddingHorizontal: 8,
        paddingVertical: 2,
        backgroundColor: COLORS.surfaceAlt,
        borderRadius: 4,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    appHeaderTagText: {
        color: COLORS.textSecondary,
        fontSize: 12,
        fontWeight: '600'
    },
    appHeaderRight: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12
    },
    headerIconBtn: {
        padding: 6,
        borderRadius: 6,
        backgroundColor: COLORS.surfaceAlt,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    headerIconText: {
        fontSize: 16
    },

    // Drawer Genre Grid styles
    drawerGenreGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        paddingHorizontal: 12,
        paddingTop: 4,
        gap: 6
    },
    drawerGenreChip: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: COLORS.surfaceAlt,
        paddingHorizontal: 8,
        paddingVertical: 5,
        borderRadius: 6,
        margin: 2
    },
    drawerGenreEmoji: {
        fontSize: 12,
        marginRight: 4
    },
    drawerGenreText: {
        color: COLORS.textSecondary,
        fontSize: 11,
        fontWeight: '600'
    }
});