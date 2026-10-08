import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { COLORS } from '../theme/colors';

/**
 * ReleaseStatusFilter - Filter component for release status
 * 
 * Statuses:
 * - Released: Now streaming
 * - Upcoming: Coming soon
 * - Ongoing: Currently airing
 * - Archive: 40+ years old content
 */
const RELEASE_STATUSES = [
    { id: null, label: 'All', icon: '🌍' },
    { id: 'released', label: 'Now Streaming', icon: '▶️', color: '#10b981' },
    { id: 'upcoming', label: 'Coming Soon', icon: '🔜', color: '#f59e0b' },
    { id: 'ongoing', label: 'Ongoing', icon: '📡', color: '#3b82f6' },
    { id: 'archive', label: 'Archive (40y+)', icon: '📦', color: '#6b7280' },
];

export function ReleaseStatusFilter({ selectedStatus, onSelect, horizontal = true }) {
    return (
        <ScrollView
            horizontal={horizontal}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.chipsRow}
        >
            {RELEASE_STATUSES.map(status => {
                const isSel = selectedStatus === status.id;
                return (
                    <TouchableOpacity
                        key={status.id || 'all'}
                        style={[
                            styles.chip,
                            isSel && styles.chipActive,
                            status.color && isSel && { borderColor: status.color }
                        ]}
                        onPress={() => onSelect(status.id)}
                    >
                        <View style={styles.chipContent}>
                            <Text style={styles.chipIcon}>{status.icon}</Text>
                            <Text style={[
                                styles.chipText,
                                isSel && styles.chipTextActive,
                                status.color && isSel && { color: status.color }
                            ]}>
                                {status.label}
                            </Text>
                        </View>
                    </TouchableOpacity>
                );
            })}
        </ScrollView>
    );
}

/**
 * ReleaseStatusBadge - Display badge for a title's release status
 */
export function ReleaseStatusBadge({ status, type }) {
    if (!status) return null;
    
    const statusConfig = RELEASE_STATUSES.find(s => s.id === status) || RELEASE_STATUSES[0];
    
    return (
        <View style={[
            styles.badge,
            statusConfig.color && { backgroundColor: `${statusConfig.color}20`, borderColor: statusConfig.color }
        ]}>
            <Text style={styles.badgeIcon}>{statusConfig.icon}</Text>
            <Text style={[
                styles.badgeText,
                statusConfig.color && { color: statusConfig.color }
            ]}>
                {statusConfig.label}
            </Text>
        </View>
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
    badge: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 3,
        paddingHorizontal: 8,
        paddingVertical: 3,
        borderRadius: 10,
        borderWidth: 1,
    },
    badgeIcon: {
        fontSize: 10,
    },
    badgeText: {
        fontSize: 10,
        fontWeight: '700',
    },
});

export default ReleaseStatusFilter;