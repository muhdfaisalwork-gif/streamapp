import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class SettingsScreen extends StatelessWidget {
  final bool isHighContrast;
  final ValueChanged<bool> onToggleHighContrast;
  final bool telemetryEnabled;
  final ValueChanged<bool> onToggleTelemetry;

  const SettingsScreen({
    Key? key,
    required this.isHighContrast,
    required this.onToggleHighContrast,
    required this.telemetryEnabled,
    required this.onToggleTelemetry,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgCanvas,
      appBar: AppBar(
        title: const Text('Settings & Preferences'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(AppTheme.space4),
        children: [
          // Accessibility Section
          const Text('Accessibility', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.brandPrimary)),
          const SizedBox(height: 8),
          SwitchListTile(
            title: const Text('High Contrast Mode', style: TextStyle(color: AppTheme.textPrimary)),
            subtitle: const Text('Replaces dark greys with pure black and luminous yellow focus borders', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
            value: isHighContrast,
            activeColor: AppTheme.focusHighContrast,
            onChanged: onToggleHighContrast,
          ),
          const Divider(color: AppTheme.bgSurface3),

          // Privacy & Diagnostics Section
          const Text('Privacy & Telemetry', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.brandPrimary)),
          const SizedBox(height: 8),
          SwitchListTile(
            title: const Text('Anonymous Diagnostic Telemetry', style: TextStyle(color: AppTheme.textPrimary)),
            subtitle: const Text('Sends zero-PII Quality of Experience (QoE) metrics to optimize streaming playback', style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
            value: telemetryEnabled,
            activeColor: AppTheme.brandPrimary,
            onChanged: onToggleTelemetry,
          ),
          const Divider(color: AppTheme.bgSurface3),

          // Legal & Copyright Notice
          const Text('Legal & Licensing Statement', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.brandPrimary)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppTheme.bgSurface2,
              borderRadius: BorderRadius.circular(AppTheme.radiusMd),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('100% Legal Open Platform', style: TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                const SizedBox(height: 4),
                const Text(
                  'All media streams hosted or indexed by this platform originate exclusively from verified public-domain collections (Archive.org, Pre-1929 classics), Creative Commons licensed independent studio works (Blender Open Movies), and public US government scientific archives (NASA). Commercial copyrighted streams are strictly banned.',
                  style: TextStyle(color: AppTheme.textSecondary, fontSize: 12, height: 1.4),
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    OutlinedButton.icon(
                      icon: const Icon(Icons.description_outlined, size: 16, color: AppTheme.brandPrimary),
                      label: const Text('Terms of Service', style: TextStyle(color: AppTheme.brandPrimary, fontSize: 12)),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppTheme.brandPrimary),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            backgroundColor: AppTheme.bgSurface1,
                            title: const Text('Terms of Service', style: TextStyle(color: AppTheme.textPrimary)),
                            content: const Text(
                              'StreamApp is an open-source, 100% legal media streaming platform. All streams are strictly limited to verified public domain, Creative Commons, or government/creator-licensed media. Commercial copyrighted streams are strictly banned. The software is provided AS-IS under open distribution principles.',
                              style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                            ),
                            actions: [
                              TextButton(
                                child: const Text('Close', style: TextStyle(color: AppTheme.brandPrimary)),
                                onPressed: () => Navigator.pop(ctx),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                    OutlinedButton.icon(
                      icon: const Icon(Icons.privacy_tip_outlined, size: 16, color: AppTheme.brandPrimary),
                      label: const Text('Privacy Policy', style: TextStyle(color: AppTheme.brandPrimary, fontSize: 12)),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppTheme.brandPrimary),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            backgroundColor: AppTheme.bgSurface1,
                            title: const Text('Privacy Policy', style: TextStyle(color: AppTheme.textPrimary)),
                            content: const Text(
                              'Zero Surveillance Pledge: StreamApp collects zero Personally Identifiable Information (PII) unless you voluntarily register. Diagnostic QoE telemetry is anonymized with ephemeral IDs, respects Do Not Track (DNT) and Global Privacy Control (GPC), and can be toggled off at any time. We never sell, share, or broker user data.',
                              style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                            ),
                            actions: [
                              TextButton(
                                child: const Text('Close', style: TextStyle(color: AppTheme.brandPrimary)),
                                onPressed: () => Navigator.pop(ctx),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                    OutlinedButton.icon(
                      icon: const Icon(Icons.gavel, size: 16, color: AppTheme.brandPrimary),
                      label: const Text('DMCA Takedown & Copyright Intake', style: TextStyle(color: AppTheme.brandPrimary, fontSize: 12)),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppTheme.brandPrimary),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      ),
                      onPressed: () {
                        showDialog(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            backgroundColor: AppTheme.bgSurface1,
                            title: const Text('DMCA Takedown Process', style: TextStyle(color: AppTheme.textPrimary)),
                            content: const Text(
                              'To report a disputed stream, send notice to legal@streaming-app.local or submit a payload to POST /api/v1/legal/takedown. Disputed titles are automatically quarantined and hidden across all clients in <60 seconds.',
                              style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                            ),
                            actions: [
                              TextButton(
                                child: const Text('Close', style: TextStyle(color: AppTheme.brandPrimary)),
                                onPressed: () => Navigator.pop(ctx),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Version & Platform Build
          Center(
            child: Text(
              'Version 1.0.0 (Build 2026.09.19) • Cross-Platform Engine',
              style: TextStyle(color: AppTheme.textMuted, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
