import React from 'react';
import { View, StyleSheet } from 'react-native';
import { COLORS } from '../theme/colors';

export default function SkeletonGrid({ count = 8, numCols = 4 }) {
    return (
        <View style={styles.grid}>
            {Array.from({ length: count }).map((_, i) => (
                <View key={i} style={[styles.card, { width: `${100 / numCols - 2}%` }]}>
                    <View style={styles.poster} />
                    <View style={styles.line1} />
                    <View style={styles.line2} />
                </View>
            ))}
        </View>
    );
}

const styles = StyleSheet.create({
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingTop: 12
    },
    card: {
        marginBottom: 20
    },
    poster: {
        width: '100%',
        aspectRatio: 2 / 3,
        backgroundColor: COLORS.surfaceAlt,
        borderRadius: 8,
        marginBottom: 8
    },
    line1: {
        height: 12,
        backgroundColor: COLORS.surfaceAlt,
        borderRadius: 4,
        width: '80%',
        marginBottom: 6
    },
    line2: {
        height: 10,
        backgroundColor: COLORS.surfaceAlt,
        borderRadius: 4,
        width: '45%'
    }
});
