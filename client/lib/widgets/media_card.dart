import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';

enum MediaCardAspectRatio {
  landscape16x9,
  portrait2x3,
}

class MediaCard extends StatefulWidget {
  final MediaItem item;
  final VoidCallback onTap;
  final MediaCardAspectRatio aspectRatio;
  final double? progressPercentage; // 0.0 to 100.0 for Continue Watching
  final bool autofocus;

  const MediaCard({
    Key? key,
    required this.item,
    required this.onTap,
    this.aspectRatio = MediaCardAspectRatio.landscape16x9,
    this.progressPercentage,
    this.autofocus = false,
  }) : super(key: key);

  @override
  State<MediaCard> createState() => _MediaCardState();
}

class _MediaCardState extends State<MediaCard> {
  bool _isFocused = false;
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final isLandscape = widget.aspectRatio == MediaCardAspectRatio.landscape16x9;
    final width = isLandscape ? 240.0 : 150.0;
    final height = isLandscape ? 135.0 : 225.0;

    final isHighlighted = _isFocused || _isHovered;

    return Focus(
      autofocus: widget.autofocus,
      onFocusChange: (focused) => setState(() => _isFocused = focused),
      child: MouseRegion(
        onEnter: (_) => setState(() => _isHovered = true),
        onExit: (_) => setState(() => _isHovered = false),
        child: GestureDetector(
          onTap: widget.onTap,
          child: AnimatedScale(
            scale: isHighlighted ? 1.08 : 1.0,
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOutCubic,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              width: width,
              height: height,
              margin: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                border: Border.all(
                  color: isHighlighted ? AppTheme.brandPrimary : Colors.transparent,
                  width: isHighlighted ? 2.5 : 1.0,
                ),
                boxShadow: isHighlighted
                    ? [
                        BoxShadow(
                          color: AppTheme.brandPrimary.withOpacity(0.35),
                          blurRadius: 16,
                          offset: const Offset(0, 6),
                        ),
                      ]
                    : [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.3),
                          blurRadius: 6,
                          offset: const Offset(0, 2),
                        ),
                      ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(AppTheme.radiusMd - 1),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    // Image with Resilient Fallback Container
                    Image.network(
                      isLandscape ? widget.item.backdropUrl : widget.item.posterUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (ctx, err, stack) => Container(
                        color: AppTheme.bgSurface2,
                        padding: const EdgeInsets.all(AppTheme.space2),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.movie_outlined, size: 36, color: AppTheme.textMuted),
                            const SizedBox(height: 6),
                            Text(
                              widget.item.title,
                              textAlign: TextAlign.center,
                              style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                    ),

                    // Hover/Focus Title Banner
                    Positioned(
                      left: 0,
                      right: 0,
                      bottom: 0,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.bottomCenter,
                            end: Alignment.topCenter,
                            colors: [
                              Colors.black.withOpacity(0.9),
                              Colors.transparent,
                            ],
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              widget.item.title,
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.textPrimary,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            Text(
                              '${widget.item.releaseYear} • ${widget.item.attribution.licenseType}',
                              style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                    ),

                    // Resolution Badge
                    Positioned(
                      top: 6,
                      right: 6,
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.7),
                          borderRadius: BorderRadius.circular(AppTheme.radiusSm),
                        ),
                        child: const Text(
                          'HD',
                          style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                        ),
                      ),
                    ),

                    // Continue Watching Progress Bar
                    if (widget.progressPercentage != null && widget.progressPercentage! > 0)
                      Positioned(
                        left: 0,
                        right: 0,
                        bottom: 0,
                        child: Container(
                          height: 4.0,
                          color: AppTheme.bgSurface3,
                          child: FractionallySizedBox(
                            alignment: Alignment.centerLeft,
                            widthFactor: (widget.progressPercentage! / 100.0).clamp(0.0, 1.0),
                            child: Container(color: AppTheme.brandPrimary),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
