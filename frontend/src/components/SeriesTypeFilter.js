import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { COLORS } from '../theme/colors';

/**
 * SeriesTypeFilter - Filter component for series type classification
 * 
 * Series Types:
 * - Fictional: Pure fiction, fantasy, sci-fi, etc.
 * - True Story: Based on real events, true crime, documentaries
 * - Historical: Set in historical periods, period dramas
 * - Biographical: Biopics, life stories of real people
 * - Historical Fiction: Fiction set in historical periods
 */
const SERIES_TYPES = [
    { id: null, label: 'All Types', icon: '📺' },
    { id: 'fictional', label: 'Fictional', icon: '🎬', color: '#6366f1' },
    { id: 'true_story', label: 'True Story', icon: '📖', color: '#10b981' },
    { id: 'historical', label: 'Historical', icon: '🏛️', color: '#f59e0b' },
    { id: 'biographical', label: 'Biographical', icon: '👤', color: '#ec4899' },
    { id: 'historical_fiction', label: 'Historical Fiction', icon: '📜', color: '#8b5cf6' },
];

export function SeriesTypeFilter({ selectedType, onSelect, horizontal = true }) {
    return (
        <ScrollView
            horizontal={horizontal}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.chipsRow}
        >
            {SERIES_TYPES.map(type => {
                const isSel = selectedType === type.id;
                return (
                    <TouchableOpacity
                        key={type.id || 'all'}
                        style={[
                            styles.chip,
                            isSel && styles.chipActive,
                            type.color && isSel && { borderColor: type.color }
                        ]}
                        onPress={() => onSelect(type.id)}
                    >
                        <View style={styles.chipContent}>
                            <Text style={styles.chipIcon}>{type.icon}</Text>
                            <Text style={[
                                styles.chipText,
                                isSel && styles.chipTextActive,
                                type.color && isSel && { color: type.color }
                            ]}>
                                {type.label}
                            </Text>
                        </View>
                    </TouchableOpacity>
                );
            })}
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    chipsRow: {
        gap: 6,
        paddingHorizontal: 16,
        paddingVertical: 4,
    },
    chip: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 16,
        borderWidth: 1,
        borderColor: COLORS.border,
        backgroundColor: COLORS.surfaceAlt,
    },
    chipActive: {
        backgroundColor: 'rgba(0, 229, 255, 0.1)',
    },
    chipContent: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
    },
    chipIcon: {
        fontSize: 14,
    },
    chipText: {
        color: COLORS.textMuted,
        fontSize: 11,
        fontWeight: '600',
    },
    chipTextActive: {
        color: COLORS.accent,
        fontWeight: '700',
    },
});

export default SeriesTypeFilter;