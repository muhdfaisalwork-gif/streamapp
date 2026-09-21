import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import '../widgets/responsive_layout.dart';
import '../widgets/sponsor_card.dart';

class MediaDetailsScreen extends StatelessWidget {
  final MediaItem item;
  final VoidCallback onPlay;
  final VoidCallback onToggleWatchlist;
  final bool isInWatchlist;
  final double? resumePercentage;

  const MediaDetailsScreen({
    Key? key,
    required this.item,
    required this.onPlay,
    required this.onToggleWatchlist,
    this.isInWatchlist = false,
    this.resumePercentage,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isPhone = ResponsiveLayout.isPhone(context);
    final hasBookmark = resumePercentage != null && resumePercentage! > 0;
    final playLabel = hasBookmark 
        ? 'Resume (${resumePercentage!.toInt()}%)' 
        : 'Play Fullscreen';

    return Scaffold(
      backgroundColor: AppTheme.bgCanvas,
      appBar: AppBar(
        title: Text(item.title),
        actions: [
          IconButton(
            icon: Icon(isInWatchlist ? Icons.bookmark : Icons.bookmark_border),
            onPressed: onToggleWatchlist,
            tooltip: 'Toggle Watchlist',
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Hero Backdrop Banner
            Stack(
              children: [
                Container(
                  height: isPhone ? 220 : 360,
                  width: double.infinity,
                  child: Image.network(
                    item.backdropUrl.isNotEmpty ? item.backdropUrl : item.posterUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (ctx, err, stack) => Container(
                      color: AppTheme.bgSurface2,
                      child: const Icon(Icons.movie, size: 64, color: AppTheme.textMuted),
                    ),
                  ),
                ),
                Container(
                  height: isPhone ? 220 : 360,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.transparent, AppTheme.bgCanvas.withOpacity(0.95), AppTheme.bgCanvas],
                    ),
                  ),
                ),
                Positioned(
                  bottom: 20,
                  left: 20,
                  child: ElevatedButton.icon(
                    onPressed: onPlay,
                    icon: const Icon(Icons.play_arrow, color: AppTheme.bgCanvas, size: 28),
                    label: Text(playLabel, style: const TextStyle(color: AppTheme.bgCanvas, fontWeight: FontWeight.bold, fontSize: 16)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.brandPrimary,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppTheme.radiusMd)),
                    ),
                  ),
                ),
              ],
            ),

            // Metadata & Details
            Padding(
              padding: const EdgeInsets.all(AppTheme.space4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Title
                  Text(item.title, style: Theme.of(context).textTheme.headlineLarge),
                  const SizedBox(height: 8),

                  // Year, Duration, Rating Row
                  Row(
                    children: [
                      Text('${item.releaseYear}', style: const TextStyle(color: AppTheme.textSecondary, fontWeight: FontWeight.w600)),
                      const SizedBox(width: 12),
                      Text('${item.durationSeconds ~/ 60} minutes', style: const TextStyle(color: AppTheme.textSecondary)),
                      const SizedBox(width: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          border: Border.all(color: AppTheme.textMuted),
                          borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                        ),
                        child: Text(item.rating, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Legal Attribution Pill (Phase 0 and 1 Mandate)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: AppTheme.brandSecondary.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                      border: Border.all(color: AppTheme.brandSecondary.withOpacity(0.5)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.verified_user_outlined, size: 18, color: AppTheme.brandPrimary),
                            const SizedBox(width: 8),
                            Text(
                              'License: ${item.attribution.licenseType}',
                              style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.textPrimary, fontSize: 13),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Creator: ${item.attribution.creator}',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
                        ),
                        if (item.attribution.sourceUrl.isNotEmpty)
                          Text(
                            'Source: ${item.attribution.sourceUrl}',
                            style: const TextStyle(color: AppTheme.brandPrimary, fontSize: 11, decoration: TextDecoration.underline),
                          ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),

                  // Genres
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: item.genres.map((g) => Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.bgSurface2,
                        borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                      ),
                      child: Text(g, style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                    )).toList(),
                  ),
                  const SizedBox(height: 20),

                  // Synopsis
                  const Text('Overview', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                  const SizedBox(height: 8),
                  Text(
                    item.description,
                    style: const TextStyle(fontSize: 15, height: 1.5, color: AppTheme.textSecondary),
                  ),
                  const SizedBox(height: 16),

                  // Ethical Creator & Archive Support Callout (Phase 6)
                  SponsorCard(
                    campaign: SponsorCampaignData(
                      id: 'sp-${item.id}',
                      title: '${item.attribution.creator} Support',
                      sponsorName: item.attribution.creator,
                      message: 'Support the artists, studios, and preservationists who made "${item.title}" free and accessible under ${item.attribution.licenseType}.',
                      ctaUrl: item.attribution.sourceUrl.isNotEmpty ? item.attribution.sourceUrl : 'https://fund.blender.org',
                      ctaLabel: 'Support Creator / Studio',
                      badgeText: 'Creator Support',
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Stream Formats Available
                  const Text('Stream Technical Details', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                  const SizedBox(height: 8),
                  ...item.sources.map((src) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.stream, color: AppTheme.brandPrimary),
                    title: Text('${src.format.toUpperCase()} (${src.resolution})', style: const TextStyle(color: AppTheme.textPrimary)),
                    subtitle: Text(src.url, style: const TextStyle(color: AppTheme.textMuted, fontSize: 11), maxLines: 1, overflow: TextOverflow.ellipsis),
                  )),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
