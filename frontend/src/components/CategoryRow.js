import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { COLORS } from '../theme/colors';
import MediaCard from './MediaCard';

export default function CategoryRow({ category, onSelectMedia, onSelectCategory }) {
    if (!category || !Array.isArray(category.items) || category.items.length === 0) {
        return null;
    }

    const items = category.items.slice(0, 30);

    return (
        <View
            style={styles.section}
            accessible={false}
            accessibilityRole="region"
        >
            <TouchableOpacity
                style={styles.header}
                onPress={() => onSelectCategory && onSelectCategory(category)}
                activeOpacity={0.75}
                accessible
                accessibilityRole="button"
                accessibilityLabel={`${category.title}, ${category.count ? category.count.toLocaleString() + ' titles' : 'browse'}`}
                accessibilityHint="Opens the full category browse page"
            >
                <View style={styles.titleWrapper}>
                    <Text style={styles.title}>{category.title}</Text>
                    {category.badge && (
                        <View style={styles.badge}>
                            <Text style={styles.badgeText}>{category.badge}</Text>
                        </View>
                    )}
                </View>
                <View style={styles.moreWrapper}>
                    <Text style={styles.countText}>
                        {category.count ? `${category.count.toLocaleString()} titles` : 'Explore'}
                    </Text>
                    <Text style={styles.arrowIcon}>›</Text>
                </View>
            </TouchableOpacity>

            <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.listContainer}
                style={{ width: '100%' }}
                accessible
                accessibilityRole="list"
                accessibilityLabel={`${category.title} carousel`}
            >
                {items.map((item, idx) => (
                    <View key={`${item.id || idx}-${idx}`} style={styles.cardWrapper}>
                        <MediaCard
                            item={item}
                            onPress={onSelectMedia}
                            showProgress
                        />
                    </View>
                ))}

                {category.count > items.length && (
                    <TouchableOpacity
                        style={styles.viewAllCard}
                        onPress={() => onSelectCategory && onSelectCategory(category)}
                        activeOpacity={0.7}
                        accessible
                        accessibilityRole="button"
                        accessibilityLabel={`View all ${category.count.toLocaleString()} titles in ${category.title}`}
                    >
                        <View style={styles.viewAllInner}>
                            <Text style={styles.viewAllIcon}>✨</Text>
                            <Text style={styles.viewAllTitle}>View All</Text>
                            <Text style={styles.viewAllCount}>{category.count.toLocaleString()} titles</Text>
                        </View>
                    </TouchableOpacity>
                )}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    section: {
        marginBottom: 28
    },
    header: {
        paddingHorizontal: 20,
        marginBottom: 14,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center'
    },
    titleWrapper: {
        flexDirection: 'row',
        alignItems: 'center',
        flex: 1
    },
    title: {
        color: COLORS.textPrimary,
        fontSize: 19,
        fontWeight: '800',
        letterSpacing: -0.3
    },
    badge: {
        marginLeft: 10,
        backgroundColor: COLORS.brand,
        paddingHorizontal: 6,
        paddingVertical: 2,
        borderRadius: 4
    },
    badgeText: {
        color: '#FFFFFF',
        fontSize: 9,
        fontWeight: '800'
    },
    moreWrapper: {
        flexDirection: 'row',
        alignItems: 'center'
    },
    countText: {
        color: COLORS.textMuted,
        fontSize: 13,
        fontWeight: '500'
    },
    arrowIcon: {
        color: COLORS.brand,
        fontSize: 18,
        fontWeight: '700',
        marginLeft: 4,
        marginTop: -2
    },
    listContainer: {
        paddingLeft: 20,
        paddingRight: 8
    },
    cardWrapper: {
        marginRight: 14
    },
    viewAllCard: {
        width: 144,
        height: 216,
        marginRight: 20,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: COLORS.border,
        borderStyle: 'dashed',
        backgroundColor: COLORS.surfaceCard,
        justifyContent: 'center',
        alignItems: 'center'
    },
    viewAllInner: {
        alignItems: 'center',
        padding: 12
    },
    viewAllIcon: {
        fontSize: 24,
        marginBottom: 6
    },
    viewAllTitle: {
        color: COLORS.textPrimary,
        fontSize: 14,
        fontWeight: '700'
    },
    viewAllCount: {
        color: COLORS.brand,
        fontSize: 11,
        fontWeight: '600',
        marginTop: 4
    }
});
