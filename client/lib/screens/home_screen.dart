import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/hero_banner.dart';
import '../widgets/tray_carousel.dart';
import '../widgets/media_card.dart';

class HomeScreen extends StatelessWidget {
  final ApiService apiService;
  final Function(MediaItem) onPlayMedia;
  final Function(MediaItem) onSelectMedia;
  final Set<String> watchlistIds;
  final Function(String) onToggleWatchlist;
  final Map<String, double> continueWatchingMap;

  const HomeScreen({
    Key? key,
    required this.apiService,
    required this.onPlayMedia,
    required this.onSelectMedia,
    required this.watchlistIds,
    required this.onToggleWatchlist,
    required this.continueWatchingMap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: apiService.getHomeFeed(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        final data = snapshot.data ?? {};
        final List<MediaItem> featured = data['featured'] ?? [];
        final List<dynamic> trays = data['trays'] ?? [];

        final heroItem = featured.isNotEmpty ? featured.first : ApiService.localFallbackCatalog.first;

        // Continue watching items
        final continueWatchingItems = ApiService.localFallbackCatalog.where(
          (m) => continueWatchingMap.containsKey(m.id) && continueWatchingMap[m.id]! > 0,
        ).toList();

        return SingleChildScrollView(
          physics: const BouncingScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Featured Spotlight Hero Banner
              HeroBanner(
                item: heroItem,
                isInWatchlist: watchlistIds.contains(heroItem.id),
                onPlay: () => onPlayMedia(heroItem),
                onWatchlistToggle: () => onToggleWatchlist(heroItem.id),
                onDetails: () => onSelectMedia(heroItem),
              ),

              const SizedBox(height: 12),

              // 2. Continue Watching Tray (if user has active bookmarks)
              if (continueWatchingItems.isNotEmpty)
                TrayCarousel(
                  title: 'Continue Watching',
                  items: continueWatchingItems,
                  aspectRatio: MediaCardAspectRatio.landscape16x9,
                  continueWatchingMap: continueWatchingMap,
                  onItemTap: onPlayMedia,
                ),

              // 3. Category Trays
              ...trays.map((tray) {
                final List<MediaItem> items = tray['items'] ?? [];
                return TrayCarousel(
                  title: tray['title'] ?? 'Trending',
                  items: items,
                  aspectRatio: MediaCardAspectRatio.landscape16x9,
                  continueWatchingMap: continueWatchingMap,
                  onItemTap: onSelectMedia,
                );
              }),

              const SizedBox(height: 32),
            ],
          ),
        );
      },
    );
  }
}
