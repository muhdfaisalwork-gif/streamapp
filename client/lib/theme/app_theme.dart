import 'package:flutter/material.dart';

class AppTheme {
  // Semantic Colors from Phase 1 Design Tokens
  static const Color bgCanvas = Color(0xFF0B0F19);
  static const Color bgSurface1 = Color(0xFF111827);
  static const Color bgSurface2 = Color(0xFF1F2937);
  static const Color bgSurface3 = Color(0xFF374151);

  static const Color brandPrimary = Color(0xFF00E5FF); // Vibrant Cyan
  static const Color brandSecondary = Color(0xFF6366F1); // Royal Indigo

  static const Color textPrimary = Color(0xFFF9FAFB);
  static const Color textSecondary = Color(0xFF9CA3AF);
  static const Color textMuted = Color(0xFF6B7280);

  static const Color statusSuccess = Color(0xFF10B981);
  static const Color statusWarning = Color(0xFFF59E0B);
  static const Color statusError = Color(0xFFEF4444);
  static const Color focusHighContrast = Color(0xFFFFE500); // High Contrast Yellow

  // 8dp Spacing Grid
  static const double space1 = 4.0;
  static const double space2 = 8.0;
  static const double space3 = 12.0;
  static const double space4 = 16.0;
  static const double space6 = 24.0;
  static const double space8 = 32.0;
  static const double space12 = 48.0;

  // Radii
  static const double radiusSm = 4.0;
  static const double radiusMd = 8.0;
  static const double radiusLg = 16.0;

  // Standard ThemeData
  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bgCanvas,
      primaryColor: brandPrimary,
      cardColor: bgSurface1,
      colorScheme: const ColorScheme.dark(
        primary: brandPrimary,
        secondary: brandSecondary,
        surface: bgSurface1,
        error: statusError,
      ),
      textTheme: const TextTheme(
        displayLarge: TextStyle(fontSize: 40, fontWeight: FontWeight.bold, color: textPrimary, letterSpacing: -0.5),
        headlineLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: textPrimary, letterSpacing: -0.25),
        headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, color: textPrimary),
        titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: textPrimary),
        bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.normal, color: textPrimary),
        bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.normal, color: textSecondary),
        bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: textMuted),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: bgCanvas,
        elevation: 0,
        centerTitle: false,
        iconTheme: IconThemeData(color: textPrimary),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: bgSurface1,
        selectedItemColor: brandPrimary,
        unselectedItemColor: textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }

  // High Contrast Mode
  static ThemeData get highContrastTheme {
    return darkTheme.copyWith(
      scaffoldBackgroundColor: Colors.black,
      cardColor: const Color(0xFF101010),
      colorScheme: const ColorScheme.dark(
        primary: focusHighContrast,
        secondary: brandPrimary,
        surface: Colors.black,
        error: statusError,
      ),
    );
  }
}
