import React, { useState } from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { COLORS } from '../theme/colors';

export default function Poster({ url, title, style, badge, resizeMode = 'cover' }) {
    const [hasError, setHasError] = useState(false);
    const validUrl = !hasError && typeof url === 'string' && url.startsWith('http') && !url.includes('/poster_') ? url : null;

    return (
        <View
            style={[styles.container, style]}
            accessible={false}
            accessibilityElementsHidden
            importantForAccessibility="no"
        >
            {validUrl ? (
                <Image
                    source={{ uri: validUrl }}
                    style={StyleSheet.absoluteFill}
                    resizeMode={resizeMode}
                    onError={() => setHasError(true)}
                    fadeDuration={100}
                    accessible={true}
                    accessibilityRole="image"
                    accessibilityLabel={title ? `Poster for ${title}` : 'Poster image'}
                    // rnw translates this to a native loading="lazy" attribute on web <img>.
                    loading="lazy"
                    decoding="async"
                />
            ) : (
                <View style={styles.fallback}>
                    <Text style={styles.fallbackIcon}>🎬</Text>
                    <Text style={styles.fallbackText} numberOfLines={2}>
                        {title || 'ShadowStream'}
                    </Text>
                </View>
            )}

            {/* Subtle bottom vignette gradient overlay */}
            <View style={styles.vignette} pointerEvents="none" />

            {badge ? (
                <View style={styles.badge}>
                    <Text style={styles.badgeText}>{badge}</Text>
                </View>
            ) : null}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        backgroundColor: COLORS.surfaceAlt,
        borderRadius: 8,
        overflow: 'hidden',
        position: 'relative'
    },
    fallback: {
        ...StyleSheet.absoluteFillObject,
        backgroundColor: COLORS.surfaceCard,
        borderWidth: 1,
        borderColor: COLORS.border,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 12
    },
    fallbackIcon: {
        fontSize: 28,
        marginBottom: 8,
        opacity: 0.8
    },
    fallbackText: {
        color: COLORS.textSecondary,
        fontSize: 11,
        fontWeight: '600',
        textAlign: 'center'
    },
    vignette: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: 48,
        backgroundColor: 'rgba(0,0,0,0.35)'
    },
    badge: {
        position: 'absolute',
        top: 8,
        right: 8,
        backgroundColor: 'rgba(10, 10, 10, 0.85)',
        paddingHorizontal: 7,
        paddingVertical: 3,
        borderRadius: 4,
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.12)'
    },
    badgeText: {
        color: '#fff',
        fontSize: 10,
        fontWeight: '700'
    }
});
