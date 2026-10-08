import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, useWindowDimensions } from 'react-native';
import { COLORS } from '../theme/colors';

export default function MobileTabBar({ navigation, activeRoute }) {
    const { width } = useWindowDimensions();
    if (width >= 768) return null; // Only show on mobile devices / small viewports

    const tabs = [
        { label: 'Home', icon: '🏠', route: 'Home' },
        { label: 'Movies', icon: '🎬', route: 'Movies' },
        { label: 'TV', icon: '📺', route: 'TV' },
        { label: 'Anime', icon: '⚡', route: 'Anime' },
        { label: 'Search', icon: '🔍', route: 'Search' },
        { label: 'Library', icon: '📚', route: 'Watchlist' }
    ];

    return (
        <View style={styles.tabBar}>
            {tabs.map(tab => {
                const isActive = activeRoute === tab.route;
                return (
                    <TouchableOpacity
                        key={tab.route}
                        style={styles.tabItem}
                        onPress={() => navigation.navigate(tab.route)}
                        activeOpacity={0.7}
                    >
                        <Text style={[styles.tabIcon, isActive && styles.tabIconActive]}>
                            {tab.icon}
                        </Text>
                        <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                            {tab.label}
                        </Text>
                    </TouchableOpacity>
                );
            })}
        </View>
    );
}

const styles = StyleSheet.create({
    tabBar: {
        height: 56,
        backgroundColor: COLORS.surface,
        borderTopWidth: 1,
        borderTopColor: COLORS.border,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-around',
        zIndex: 100
    },
    tabItem: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: 4
    },
    tabIcon: {
        fontSize: 18,
        opacity: 0.7,
        marginBottom: 2
    },
    tabIconActive: {
        opacity: 1,
        transform: [{ scale: 1.1 }]
    },
    tabLabel: {
        color: COLORS.textMuted,
        fontSize: 10,
        fontWeight: '600'
    },
    tabLabelActive: {
        color: COLORS.brandSecondary,
        fontWeight: '700'
    }
});
