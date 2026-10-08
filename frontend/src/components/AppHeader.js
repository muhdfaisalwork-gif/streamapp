import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, useWindowDimensions } from 'react-native';
import { COLORS } from '../theme/colors';
import { Storage } from '../utils/storage';

export default function AppHeader({ navigation, activeRoute, title }) {
    const { width } = useWindowDimensions();
    const isDesktop = width >= 1024;
    const isTablet = width >= 768 && width < 1024;
    const isMobile = width < 768;

    const [watchlistCount, setWatchlistCount] = useState(0);

    useEffect(() => {
        const updateCount = () => {
            const list = Storage.get('watchlist', []);
            setWatchlistCount(Array.isArray(list) ? list.length : 0);
        };
        updateCount();
        const interval = setInterval(updateCount, 2500);
        return () => clearInterval(interval);
    }, []);

    const toggleDrawer = () => {
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

    const navItems = [
        { label: 'Home', route: 'Home' },
        { label: 'Movies', route: 'Movies' },
        { label: 'TV Shows', route: 'TV' },
        { label: 'Anime', route: 'Anime' },
        { label: 'Short TV', route: 'ShortDramas' },
        { label: 'Countries', route: 'Countries' },
        { label: 'Languages', route: 'Languages' },
        { label: 'Collections', route: 'Collections' },
        { label: 'Blogs', route: 'Blogs' },
        { label: 'Apps', route: 'Apps' }
    ];

    return (
        <View style={styles.header}>
            <View style={styles.leftSection}>
                {isMobile && (
                    <TouchableOpacity
                        style={styles.hamburgerBtn}
                        onPress={toggleDrawer}
                        hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
                    >
                        <Text style={styles.hamburgerIcon}>☰</Text>
                    </TouchableOpacity>
                )}

                <TouchableOpacity
                    style={styles.brandContainer}
                    onPress={() => navigation.navigate('Home')}
                    activeOpacity={0.8}
                >
                    <View style={styles.logoBadge}>
                        <Text style={styles.logoIcon}>🎬</Text>
                    </View>
                    <View>
                        <Text style={styles.brandTitle}>
                            SHADOW<Text style={{ color: COLORS.brand }}>STREAM</Text>
                        </Text>
                        <Text style={styles.brandSub}>CINEMATIC DISCOVERY</Text>
                    </View>
                </TouchableOpacity>

                {title && (
                    <View style={styles.screenTag}>
                        <Text style={styles.screenTagText}>{title}</Text>
                    </View>
                )}
            </View>

            {/* Desktop Navigation Links */}
            {(isDesktop || isTablet) && (
                <View style={styles.navLinksRow}>
                    {navItems.slice(0, isTablet ? 6 : navItems.length).map(item => {
                        const isActive = activeRoute === item.route;
                        return (
                            <TouchableOpacity
                                key={item.route}
                                style={[styles.navLink, isActive && styles.navLinkActive]}
                                onPress={() => navigation.navigate(item.route)}
                            >
                                <Text style={[styles.navLinkText, isActive && styles.navLinkTextActive]}>
                                    {item.label}
                                </Text>
                            </TouchableOpacity>
                        );
                    })}
                </View>
            )}

            {/* Right Action Icons (Search, Watchlist, History) */}
            <View style={styles.rightSection}>
                <TouchableOpacity
                    style={styles.actionBtn}
                    onPress={() => navigation.navigate('Search')}
                    accessibilityLabel="Search"
                >
                    <Text style={styles.actionIcon}>🔍</Text>
                    {isDesktop && <Text style={styles.actionBtnLabel}>Search</Text>}
                </TouchableOpacity>

                <TouchableOpacity
                    style={styles.actionBtn}
                    onPress={() => navigation.navigate('Watchlist')}
                    accessibilityLabel="Watchlist"
                >
                    <View style={{ position: 'relative' }}>
                        <Text style={styles.actionIcon}>🔖</Text>
                        {watchlistCount > 0 && (
                            <View style={styles.badgeCounter}>
                                <Text style={styles.badgeCounterText}>
                                    {watchlistCount > 99 ? '99+' : watchlistCount}
                                </Text>
                            </View>
                        )}
                    </View>
                    {isDesktop && <Text style={styles.actionBtnLabel}>Watchlist</Text>}
                </TouchableOpacity>

                <TouchableOpacity
                    style={styles.actionBtn}
                    onPress={() => navigation.navigate('History')}
                    accessibilityLabel="History"
                >
                    <Text style={styles.actionIcon}>🕒</Text>
                    {isDesktop && <Text style={styles.actionBtnLabel}>History</Text>}
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    header: {
        height: 64,
        backgroundColor: COLORS.surface,
        borderBottomWidth: 1,
        borderBottomColor: COLORS.border,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 18,
        zIndex: 100
    },
    leftSection: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    hamburgerBtn: {
        paddingRight: 14,
        paddingVertical: 6
    },
    hamburgerIcon: {
        color: COLORS.textPrimary,
        fontSize: 22
    },
    brandContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        marginRight: 24
    },
    logoBadge: {
        width: 34,
        height: 34,
        borderRadius: 8,
        backgroundColor: COLORS.surfaceAlt,
        borderWidth: 1,
        borderColor: 'rgba(229, 9, 20, 0.4)',
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 10
    },
    logoIcon: {
        fontSize: 18
    },
    brandTitle: {
        color: COLORS.textPrimary,
        fontSize: 18,
        fontWeight: '900',
        letterSpacing: 1
    },
    brandSub: {
        color: COLORS.textMuted,
        fontSize: 7.5,
        fontWeight: '700',
        letterSpacing: 1.2
    },
    screenTag: {
        marginLeft: 12,
        backgroundColor: COLORS.surfaceAlt,
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 4,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    screenTagText: {
        color: COLORS.textSecondary,
        fontSize: 11,
        fontWeight: '600'
    },
    navLinksRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4
    },
    navLink: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 6
    },
    navLinkActive: {
        backgroundColor: 'rgba(229, 9, 20, 0.15)'
    },
    navLinkText: {
        color: COLORS.textSecondary,
        fontSize: 13,
        fontWeight: '600'
    },
    navLinkTextActive: {
        color: COLORS.brandSecondary,
        fontWeight: '700'
    },
    rightSection: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8
    },
    actionBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: 6,
        backgroundColor: COLORS.surfaceAlt,
        borderWidth: 1,
        borderColor: COLORS.border
    },
    actionIcon: {
        fontSize: 15
    },
    actionBtnLabel: {
        color: COLORS.textPrimary,
        fontSize: 12,
        fontWeight: '600',
        marginLeft: 6
    },
    badgeCounter: {
        position: 'absolute',
        top: -6,
        right: -8,
        backgroundColor: COLORS.brand,
        borderRadius: 9,
        minWidth: 16,
        height: 16,
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 3
    },
    badgeCounterText: {
        color: '#FFFFFF',
        fontSize: 9,
        fontWeight: '800'
    }
});
