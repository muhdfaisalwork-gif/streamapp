import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import 'media_card.dart';

class TrayCarousel extends StatelessWidget {
  final String title;
  final List<MediaItem> items;
  final Function(MediaItem) onItemTap;
  final MediaCardAspectRatio aspectRatio;
  final Map<String, double>? continueWatchingMap;

  const TrayCarousel({
    Key? key,
    required this.title,
    required this.items,
    required this.onItemTap,
    this.aspectRatio = MediaCardAspectRatio.landscape16x9,
    this.continueWatchingMap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();

    final isLandscape = aspectRatio == MediaCardAspectRatio.landscape16x9;
    final trayHeight = isLandscape ? 175.0 : 265.0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Tray Section Header
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppTheme.space4, vertical: AppTheme.space2),
          child: Text(
            title,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),

        // Horizontal Carousel
        SizedBox(
          height: trayHeight,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: AppTheme.space3),
            itemCount: items.length,
            physics: const BouncingScrollPhysics(),
            itemBuilder: (context, index) {
              final item = items[index];
              final progress = continueWatchingMap?[item.id];
              return MediaCard(
                key: ValueKey('media-card-${item.id}'),
                item: item,
                aspectRatio: aspectRatio,
                progressPercentage: progress,
                onTap: () => onItemTap(item),
              );
            },
          ),
        ),
      ],
    );
  }
}
