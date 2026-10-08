import React, { useState, useEffect, useCallback } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity,
    SafeAreaView, ActivityIndicator, useWindowDimensions
} from 'react-native';
import { COLORS } from '../theme/colors';
import AppHeader from '../components/AppHeader';
import MobileTabBar from '../components/MobileTabBar';
import MediaCard from '../components/MediaCard';
import SkeletonGrid from '../components/SkeletonGrid';
import SeriesTypeFilter from '../components/SeriesTypeFilter';
import ReleaseStatusFilter from '../components/ReleaseStatusFilter';
import { getApiBase } from '../utils/api';
import { useRouteMeta } from '../utils/useRouteMeta';

export default function BrowseScreen({ route, navigation }) {
    const { width } = useWindowDimensions();
    const isDesktop = width >= 1024;
    const numCols = width >= 1400 ? 6 : width >= 1024 ? 5 : width >= 768 ? 4 : width >= 480 ? 3 : 2;

    useRouteMeta('Browse');
    const [activeTab, setActiveTab] = useState(route?.params?.categoryId || 'movie');
    const [selectedSort, setSelectedSort] = useState('popularity');
    const [selectedGenre, setSelectedGenre] = useState(null);
    const [selectedCountry, setSelectedCountry] = useState(null);
    const [selectedAudioLang, setSelectedAudioLang] = useState(null);
    const [selectedSeriesType, setSelectedSeriesType] = useState(null);
    const [selectedReleaseStatus, setSelectedReleaseStatus] = useState(null);
    const [selectedYearMin, setSelectedYearMin] = useState(null);
    const [showFilters, setShowFilters] = useState(false);

    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);

    const tabs = [
        { id: 'movie', label: '🎬 Movies' },
        { id: 'tv', label: '📺 TV Series' },
        { id: 'anime', label: '🌸 Anime' },
        { id: 'short_drama', label: '📱 Short TV' }
    ];

    const sorts = [
        { id: 'popularity', label: 'Most Popular' },
        { id: 'rating', label: 'Top Rated' },
        { id: 'year', label: 'Latest Release' }
    ];

    const genres = [
        { id: null, label: 'All Genres' },
        { id: 'Action', label: 'Action' },
        { id: 'Comedy', label: 'Comedy' },
        { id: 'Drama', label: 'Drama' },
        { id: 'Sci-Fi', label: 'Sci-Fi' },
        { id: 'Horror', label: 'Horror' },
        { id: 'Romance', label: 'Romance' },
        { id: 'Thriller', label: 'Thriller' }
    ];

    const countries = [
        { id: null, label: 'All Origins' },
        { id: 'US', label: '🇺🇸 US' },
        { id: 'KR', label: '🇰🇷 Korea' },
        { id: 'JP', label: '🇯🇵 Japan' },
        { id: 'IN', label: '🇮🇳 India' },
        { id: 'GB', label: '🇬🇧 UK' },
        { id: 'FR', label: '🇫🇷 France' }
    ];

    const audioLanguages = [
        { id: null, label: 'Any Audio' },
        { id: 'en', label: 'English' },
        { id: 'ja', label: 'Japanese' },
        { id: 'ko', label: 'Korean' },
        { id: 'hi', label: 'Hindi' },
        { id: 'es', label: 'Spanish' }
    ];

    const yearBuckets = [
        { id: null, label: 'All Years' },
        { id: 2024, label: '2024+' },
        { id: 2020, label: '2020s' },
        { id: 2010, label: '2010s' },
        { id: 2000, label: '2000s' },
        { id: 1990, label: '1990s' },
        { id: 1980, label: '1980s' }
    ];

    const seriesTypes = [
        { id: null, label: 'All Types' },
        { id: 'fictional', label: 'Fictional' },
        { id: 'true_story', label: 'True Story' },
        { id: 'historical', label: 'Historical' },
        { id: 'biographical', label: 'Biographical' },
        { id: 'historical_fiction', label: 'Historical Fiction' }
    ];

    const releaseStatuses = [
        { id: null, label: 'All Status' },
        { id: 'released', label: 'Now Streaming' },
        { id: 'upcoming', label: 'Coming Soon' },
        { id: 'ongoing', label: 'Ongoing' },
        { id: 'archive', label: 'Archive (40y+)' }
    ];

    const fetchItems = useCallback(async (tab, sort, genre, country, audio, seriesType, releaseStatus, yearMin, pageNum, append = false) => {
        if (pageNum === 1) setLoading(true);
        else setLoadingMore(true);

        try {
            let url = `${getApiBase()}/titles?page=${pageNum}&page_size=24&sort=${sort}`;
            if (tab === 'anime') url += '&type=anime';
            else if (tab === 'short_drama') url += '&type=short_drama';
            else if (tab === 'tv') url += '&type=tv';
            else url += '&type=movie';

            if (genre) url += `&genre=${encodeURIComponent(genre)}`;
            if (country) url += `&country=${encodeURIComponent(country)}`;
            if (audio) url += `&audio_language=${encodeURIComponent(audio)}`;
            if (seriesType) url += `&series_type=${encodeURIComponent(seriesType)}`;
            if (releaseStatus) url += `&release_status=${encodeURIComponent(releaseStatus)}`;
            if (yearMin) url += `&year_min=${yearMin}`;

            const res = await fetch(url);
            if (res.ok) {
                const data = await res.json();
                const newItems = data.items || [];
                setTotal(data.total || 0);
                if (append) {
                    setItems(prev => [...prev, ...newItems]);
                } else {
                    setItems(newItems);
                }
            }
        } catch (err) {
            console.error('[BrowseScreen] fetchItems error:', err);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, []);

    useEffect(() => {
        setPage(1);
        fetchItems(activeTab, selectedSort, selectedGenre, selectedCountry, selectedAudioLang, selectedSeriesType, selectedReleaseStatus, selectedYearMin, 1, false);
    }, [activeTab, selectedSort, selectedGenre, selectedCountry, selectedAudioLang, selectedSeriesType, selectedReleaseStatus, selectedYearMin, fetchItems]);

    const handleLoadMore = () => {
        if (loadingMore || items.length >= total) return;
        const nextPage = page + 1;
        setPage(nextPage);
        fetchItems(activeTab, selectedSort, selectedGenre, selectedCountry, selectedAudioLang, selectedSeriesType, selectedReleaseStatus, selectedYearMin, nextPage, true);
    };

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} activeRoute="Browse" title="Browse Catalog" />

            <ScrollView showsVerticalScrollIndicator={false}>
                <View style={styles.hubHero}>
                    <View style={styles.heroTopRow}>
                        <View>
                            <Text style={styles.hubTitle}>🌍 Global Catalog</Text>
                            <Text style={styles.hubSub}>
                                {total.toLocaleString()} titles available.
                            </Text>
                        </View>
                        <TouchableOpacity style={styles.toggleFilterBtn} onPress={() => setShowFilters(!showFilters)}>
                            <Text style={styles.toggleFilterText}>{showFilters ? 'Hide Filters' : 'Show Filters'}</Text>
                        </TouchableOpacity>
                    </View>
                </View>

                {/* Sub-tabs Row (Media Type) */}
                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabsRow}>
                    {tabs.map(tab => {
                        const isActive = activeTab === tab.id;
                        return (
                            <TouchableOpacity
                                key={tab.id}
                                style={[styles.tabChip, isActive && styles.tabChipActive]}
                                onPress={() => setActiveTab(tab.id)}
                            >
                                <Text style={[styles.tabChipText, isActive && styles.tabChipTextActive]}>
                                    {tab.label}
                                </Text>
                            </TouchableOpacity>
                        );
                    })}
                </ScrollView>

                {showFilters && (
                    <View style={styles.filtersContainer}>
                        {/* Sort */}
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChipsRow}>
                            {sorts.map(s => {
                                const isSel = selectedSort === s.id;
                                return (
                                    <TouchableOpacity key={s.id} style={[styles.filterChip, isSel && styles.filterChipActive]} onPress={() => setSelectedSort(s.id)}>
                                        <Text style={[styles.filterChipText, isSel && styles.filterChipTextActive]}>{s.label}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>
                        
                        {/* Genre */}
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChipsRow}>
                            {genres.map(g => {
                                const isSel = selectedGenre === g.id;
                                return (
                                    <TouchableOpacity key={g.label} style={[styles.filterChip, isSel && styles.filterChipActive]} onPress={() => setSelectedGenre(g.id)}>
                                        <Text style={[styles.filterChipText, isSel && styles.filterChipTextActive]}>{g.label}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>

                        {/* Country */}
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChipsRow}>
                            {countries.map(c => {
                                const isSel = selectedCountry === c.id;
                                return (
                                    <TouchableOpacity key={c.label} style={[styles.filterChip, isSel && styles.filterChipActive]} onPress={() => setSelectedCountry(c.id)}>
                                        <Text style={[styles.filterChipText, isSel && styles.filterChipTextActive]}>{c.label}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>

                        {/* Audio Language */}
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChipsRow}>
                            {audioLanguages.map(a => {
                                const isSel = selectedAudioLang === a.id;
                                return (
                                    <TouchableOpacity key={a.label} style={[styles.filterChip, isSel && styles.filterChipActive]} onPress={() => setSelectedAudioLang(a.id)}>
                                        <Text style={[styles.filterChipText, isSel && styles.filterChipTextActive]}>{a.label}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>

                        {/* Series Type */}
                        <SeriesTypeFilter
                            selectedType={selectedSeriesType}
                            onSelect={setSelectedSeriesType}
                        />

                        {/* Release Status */}
                        <ReleaseStatusFilter
                            selectedStatus={selectedReleaseStatus}
                            onSelect={setSelectedReleaseStatus}
                        />

                        {/* Year */}
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterChipsRow}>
                            {yearBuckets.map(y => {
                                const isSel = selectedYearMin === y.id;
                                return (
                                    <TouchableOpacity key={y.label} style={[styles.filterChip, isSel && styles.filterChipActive]} onPress={() => setSelectedYearMin(y.id)}>
                                        <Text style={[styles.filterChipText, isSel && styles.filterChipTextActive]}>{y.label}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>
                    </View>
                )}

                {/* Grid */}
                {loading ? (
                    <SkeletonGrid count={8} numCols={numCols} />
                ) : items.length === 0 ? (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No titles found matching your filters.</Text>
                    </View>
                ) : (
                    <View style={styles.grid}>
                        {items.map((it, idx) => (
                            <View
                                key={`${it.id || idx}-${idx}`}
                                style={{ width: `${100 / numCols - 1.5}%`, marginBottom: 18 }}
                            >
                                <MediaCard
                                    item={it}
                                    onPress={(item) => navigation.navigate('TitleDetail', { slug: item.slug || String(item.id), item })}
                                    isLarge={isDesktop}
                                />
                            </View>
                        ))}
                    </View>
                )}

                {/* Load More Button */}
                {items.length < total && !loading && (
                    <View style={styles.loadMoreRow}>
                        <TouchableOpacity
                            style={styles.loadMoreBtn}
                            onPress={handleLoadMore}
                            disabled={loadingMore}
                        >
                            {loadingMore ? (
                                <ActivityIndicator size="small" color="#FFFFFF" />
                            ) : (
                                <Text style={styles.loadMoreBtnText}>
                                    Load More ({items.length} of {total.toLocaleString()})
                                </Text>
                            )}
                        </TouchableOpacity>
                    </View>
                )}

                <View style={{ height: 40 }} />
            </ScrollView>

            <MobileTabBar navigation={navigation} activeRoute="Browse" />
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    screen: { flex: 1, backgroundColor: COLORS.bg },
    hubHero: { paddingHorizontal: 20, paddingTop: 20, paddingBottom: 14 },
    heroTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    hubTitle: { color: COLORS.textPrimary, fontSize: 26, fontWeight: '900', letterSpacing: -0.5 },
    hubSub: { color: COLORS.textMuted, fontSize: 13, marginTop: 4 },
    toggleFilterBtn: { paddingHorizontal: 12, paddingVertical: 6, backgroundColor: COLORS.surfaceAlt, borderRadius: 6, borderWidth: 1, borderColor: COLORS.border },
    toggleFilterText: { color: COLORS.brand, fontSize: 12, fontWeight: '700' },
    tabsRow: { paddingHorizontal: 16, paddingVertical: 6, gap: 8 },
    tabChip: {
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 20,
        backgroundColor: COLORS.surfaceAlt,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    tabChipActive: { backgroundColor: COLORS.brand, borderColor: COLORS.brand },
    tabChipText: { color: COLORS.textSecondary, fontSize: 12, fontWeight: '600' },
    tabChipTextActive: { color: '#FFFFFF', fontWeight: '700' },
    filtersContainer: {
        paddingVertical: 10,
        backgroundColor: '#111111',
        borderTopWidth: 1,
        borderBottomWidth: 1,
        borderColor: COLORS.border,
        marginBottom: 10
    },
    filterChipsRow: {
        paddingHorizontal: 16,
        paddingVertical: 6,
        gap: 6
    },
    filterChip: {
        paddingHorizontal: 10,
        paddingVertical: 5,
        borderRadius: 6,
        borderWidth: 1,
        borderColor: COLORS.border,
        backgroundColor: COLORS.surfaceAlt
    },
    filterChipActive: {
        borderColor: COLORS.accent,
        backgroundColor: 'rgba(0, 229, 255, 0.1)'
    },
    filterChipText: {
        color: COLORS.textMuted,
        fontSize: 11,
        fontWeight: '600'
    },
    filterChipTextActive: {
        color: COLORS.accent,
        fontWeight: '700'
    },
    emptyState: { padding: 40, alignItems: 'center' },
    emptyText: { color: COLORS.textMuted, fontSize: 14 },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingTop: 10
    },
    loadMoreRow: { alignItems: 'center', paddingVertical: 24 },
    loadMoreBtn: {
        backgroundColor: COLORS.surfaceAlt,
        borderWidth: 1,
        borderColor: COLORS.border,
        paddingHorizontal: 24,
        paddingVertical: 12,
        borderRadius: 8
    },
    loadMoreBtnText: { color: COLORS.textPrimary, fontSize: 13, fontWeight: '700' }
});