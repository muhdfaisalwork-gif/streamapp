import React, { useState, useEffect } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity,
    SafeAreaView, ActivityIndicator, useWindowDimensions
} from 'react-native';
import { COLORS } from '../theme/colors';
import AppHeader from '../components/AppHeader';
import MobileTabBar from '../components/MobileTabBar';
import Poster from '../components/Poster';
import MediaCard from '../components/MediaCard';
import SkeletonGrid from '../components/SkeletonGrid';
import { getApiBase } from '../utils/api';
import { useRouteMeta } from '../utils/useRouteMeta';

export default function CollectionDetailScreen({ route, navigation }) {
    const rawCollection = route?.params?.collection;
    const slug = route?.params?.slug || (typeof rawCollection === 'string' ? rawCollection : rawCollection?.slug || rawCollection?.id) || '';
    const [collection, setCollection] = useState(() => {
        if (rawCollection && typeof rawCollection === 'object') return rawCollection;
        return { slug, name: slug.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) };
    });

    const { width } = useWindowDimensions();
    const isDesktop = width >= 1024;
    const numCols = width >= 1400 ? 6 : width >= 1024 ? 5 : width >= 768 ? 4 : width >= 480 ? 3 : 2;

    useRouteMeta('CollectionDetail', collection);
    const [titles, setTitles] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        const slugOrId = collection.slug || slug || collection.id;
        fetch(`${getApiBase()}/titles?collection=${encodeURIComponent(slugOrId)}&page_size=60`)
            .then(r => r.json())
            .then(d => {
                if (!cancelled) {
                    if (d.collection) {
                        setCollection(d.collection);
                    }
                    let items = d.items || (Array.isArray(d) ? d : []);
                    if (items.length === 0 && (collection.name || slug)) {
                        // Fallback search by collection name or slug
                        fetch(`${getApiBase()}/search?q=${encodeURIComponent(collection.slug || slug || collection.name)}&limit=40`)
                            .then(r2 => r2.json())
                            .then(d2 => {
                                if (!cancelled) {
                                    setTitles(d2.items || []);
                                    setLoading(false);
                                }
                            })
                            .catch(() => {
                                if (!cancelled) setLoading(false);
                            });
                    } else {
                        setTitles(items);
                        setLoading(false);
                    }
                }
            })
            .catch(() => {
                if (!cancelled) setLoading(false);
            });
        return () => { cancelled = true; };
    }, [collection.slug, collection.id, collection.name, slug]);

    return (
        <SafeAreaView style={styles.screen}>
            <AppHeader navigation={navigation} activeRoute="Collections" title={collection.name || 'Collection'} />

            <ScrollView showsVerticalScrollIndicator={false}>
                {/* Collection Hero Header */}
                <View style={styles.headerHero}>
                    <Poster
                        url={collection.cover_image || collection.poster}
                        title={collection.name}
                        style={StyleSheet.absoluteFill}
                    />
                    <View style={styles.heroOverlay}>
                        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
                            <Text style={styles.backBtnText}>â€¹ All Collections</Text>
                        </TouchableOpacity>

                        <View style={styles.badge}>
                            <Text style={styles.badgeText}>CURATED UNIVERSE</Text>
                        </View>

                        <Text style={styles.heroTitle}>{collection.name}</Text>
                        <Text style={styles.heroDesc}>{collection.description || 'Collection of cinematic titles.'}</Text>
                        <Text style={styles.heroMeta}>
                            {titles.length} titles in chronological & release order
                        </Text>
                    </View>
                </View>

                {/* Titles Grid */}
                {loading ? (
                    <SkeletonGrid count={8} numCols={numCols} />
                ) : (
                    <View style={styles.grid}>
                        {titles.map((t, idx) => (
                            <View
                                key={`${t.id || idx}-${idx}`}
                                style={{ width: `${100 / numCols - 1.5}%`, marginBottom: 18 }}
                            >
                                <MediaCard
                                    item={t}
                                    onPress={(it) => navigation.navigate('TitleDetail', { slug: it.slug || String(it.id), item: it })}
                                    isLarge={isDesktop}
                                />
                            </View>
                        ))}
                    </View>
                )}

                <View style={{ height: 40 }} />
            </ScrollView>

            <MobileTabBar navigation={navigation} activeRoute="Collections" />
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    screen: { flex: 1, backgroundColor: COLORS.bg },
    headerHero: {
        height: 240,
        position: 'relative',
        justifyContent: 'flex-end',
        backgroundColor: COLORS.surface
    },
    heroOverlay: {
        padding: 20,
        backgroundColor: 'rgba(10, 10, 10, 0.8)',
        width: '100%'
    },
    backBtn: { marginBottom: 10 },
    backBtnText: { color: COLORS.brand, fontSize: 13, fontWeight: '700' },
    badge: {
        alignSelf: 'flex-start',
        backgroundColor: COLORS.brand,
        paddingHorizontal: 7,
        paddingVertical: 2,
        borderRadius: 4,
        marginBottom: 6
    },
    badgeText: { color: '#FFFFFF', fontSize: 9, fontWeight: '800' },
    heroTitle: { color: COLORS.textPrimary, fontSize: 24, fontWeight: '900', marginBottom: 4 },
    heroDesc: { color: COLORS.textSecondary, fontSize: 12, lineHeight: 18, marginBottom: 8, maxWidth: 640 },
    heroMeta: { color: COLORS.textMuted, fontSize: 11, fontWeight: '600' },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingTop: 16
    }
});



