import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import 'responsive_layout.dart';

class HeroBanner extends StatelessWidget {
  final MediaItem item;
  final VoidCallback onPlay;
  final VoidCallback onWatchlistToggle;
  final VoidCallback onDetails;
  final bool isInWatchlist;

  const HeroBanner({
    Key? key,
    required this.item,
    required this.onPlay,
    required this.onWatchlistToggle,
    required this.onDetails,
    this.isInWatchlist = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isPhone = ResponsiveLayout.isPhone(context);
    final height = isPhone 
      ? MediaQuery.of(context).size.height * 0.45 
      : MediaQuery.of(context).size.height * 0.58;

    return Semantics(
      container: true,
      label: 'Featured presentation: ${item.title}. ${item.description}',
      child: Container(
        height: height,
        width: double.infinity,
        child: Stack(
          fit: StackFit.expand,
          children: [
          // 1. Backdrop Image with Fallback
          Image.network(
            item.backdropUrl.isNotEmpty ? item.backdropUrl : item.posterUrl,
            fit: BoxFit.cover,
            errorBuilder: (ctx, err, stack) => Container(
              color: AppTheme.bgSurface2,
              child: const Center(
                child: Icon(Icons.movie_outlined, size: 64, color: AppTheme.textMuted),
              ),
            ),
          ),

          // 2. Multi-stage Gradient Scrim (Phase 1 Token Specification)
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.transparent,
                  AppTheme.bgCanvas.withOpacity(0.4),
                  AppTheme.bgCanvas.withOpacity(0.95),
                  AppTheme.bgCanvas,
                ],
                stops: const [0.0, 0.4, 0.8, 1.0],
              ),
            ),
          ),

          // Horizontal Vignette for Wide Displays
          if (!isPhone)
            Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.centerLeft,
                  end: Alignment.centerRight,
                  colors: [
                    AppTheme.bgCanvas.withOpacity(0.95),
                    AppTheme.bgCanvas.withOpacity(0.5),
                    Colors.transparent,
                  ],
                  stops: const [0.0, 0.35, 0.7],
                ),
              ),
            ),

          // 3. Content Details & Action CTAs
          Positioned(
            left: isPhone ? AppTheme.space4 : AppTheme.space8,
            right: isPhone ? AppTheme.space4 : AppTheme.space12,
            bottom: AppTheme.space6,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                // Legal & Quality Badges
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.brandSecondary.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                        border: Border.all(color: AppTheme.brandSecondary),
                      ),
                      child: Text(
                        item.attribution.licenseType,
                        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 11, fontWeight: FontWeight.bold),
                      ),
                    ),
                    const SizedBox(width: AppTheme.space2),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.bgSurface3,
                        borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                      ),
                      child: Text(
                        '${item.releaseYear} • ${item.durationSeconds ~/ 60}m',
                        style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppTheme.space2),

                // Title
                Text(
                  item.title,
                  style: isPhone
                      ? Theme.of(context).textTheme.headlineLarge
                      : Theme.of(context).textTheme.displayLarge,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: AppTheme.space1),

                // Description Synopsis
                Text(
                  item.description,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                  maxLines: isPhone ? 2 : 3,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: AppTheme.space4),

                // Action Buttons Row
                Row(
                  children: [
                    // Play Now CTA
                    ElevatedButton.icon(
                      onPressed: onPlay,
                      icon: const Icon(Icons.play_arrow, color: AppTheme.bgCanvas),
                      label: const Text('Play Now', style: TextStyle(color: AppTheme.bgCanvas, fontWeight: FontWeight.bold)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.brandPrimary,
                        padding: EdgeInsets.symmetric(
                          horizontal: isPhone ? 16 : 24,
                          vertical: isPhone ? 12 : 16,
                        ),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppTheme.radiusMd)),
                      ),
                    ),
                    const SizedBox(width: AppTheme.space3),

                    // Watchlist Toggle
                    OutlinedButton.icon(
                      onPressed: onWatchlistToggle,
                      icon: Icon(
                        isInWatchlist ? Icons.check : Icons.add,
                        color: AppTheme.textPrimary,
                      ),
                      label: Text(
                        isInWatchlist ? 'In Watchlist' : 'Watchlist',
                        style: const TextStyle(color: AppTheme.textPrimary),
                      ),
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: AppTheme.bgSurface3),
                        backgroundColor: AppTheme.bgSurface1.withOpacity(0.7),
                        padding: EdgeInsets.symmetric(
                          horizontal: isPhone ? 14 : 20,
                          vertical: isPhone ? 12 : 16,
                        ),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppTheme.radiusMd)),
                      ),
                    ),
                    const SizedBox(width: AppTheme.space2),

                    // More Info Button
                    IconButton(
                      onPressed: onDetails,
                      icon: const Icon(Icons.info_outline, color: AppTheme.textSecondary),
                      tooltip: 'Details & Attribution',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}
}
