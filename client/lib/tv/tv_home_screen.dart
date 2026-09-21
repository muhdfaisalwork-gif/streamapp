import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/hero_banner.dart';
import 'tv_focus_engine.dart';

class TvHomeScreen extends StatefulWidget {
  final ApiService apiService;
  final Function(MediaItem) onPlayMedia;
  final Function(MediaItem) onSelectMedia;
  final Set<String> watchlistIds;
  final Function(String) onToggleWatchlist;
  final Map<String, double> continueWatchingMap;

  const TvHomeScreen({
    Key? key,
    required this.apiService,
    required this.onPlayMedia,
    required this.onSelectMedia,
    required this.watchlistIds,
    required this.onToggleWatchlist,
    required this.continueWatchingMap,
  }) : super(key: key);

  @override
  State<TvHomeScreen> createState() => _TvHomeScreenState();
}

class _TvHomeScreenState extends State<TvHomeScreen> {
  bool _drawerExpanded = false;
  int _selectedNavIndex = 0;
  final ScrollController _verticalScroll = ScrollController();

  final List<Map<String, dynamic>> _navDestinations = [
    {'icon': Icons.home, 'label': 'Home'},
    {'icon': Icons.search, 'label': 'Search'},
    {'icon': Icons.bookmark, 'label': 'Watchlist'},
    {'icon': Icons.settings, 'label': 'Settings'},
  ];

  @override
  void dispose() {
    _verticalScroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.bgCanvas,
      body: Row(
        children: [
          // 1. Android TV Expandable Navigation Drawer (10-Foot Focusable)
          FocusScope(
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              width: _drawerExpanded ? 220 : 72,
              color: AppTheme.bgSurface1,
              child: Column(
                children: [
                  const SizedBox(height: 36),
                  const Icon(Icons.play_circle_fill, size: 36, color: AppTheme.brandPrimary),
                  const SizedBox(height: 28),
                  Expanded(
                    child: ListView.builder(
                      itemCount: _navDestinations.length,
                      itemBuilder: (context, index) {
                        final item = _navDestinations[index];
                        final isSelected = _selectedNavIndex == index;

                        return Focus(
                          onFocusChange: (focused) {
                            if (focused) {
                              setState(() {
                                _drawerExpanded = true;
                                _selectedNavIndex = index;
                              });
                            }
                          },
                          child: InkWell(
                            onTap: () => setState(() => _selectedNavIndex = index),
                            child: Container(
                              height: 54,
                              padding: const EdgeInsets.symmetric(horizontal: 16),
                              child: Row(
                                children: [
                                  Icon(
                                    item['icon'],
                                    color: isSelected ? AppTheme.brandPrimary : AppTheme.textMuted,
                                    size: 26,
                                  ),
                                  if (_drawerExpanded) ...[
                                    const SizedBox(width: 16),
                                    Text(
                                      item['label'],
                                      style: TextStyle(
                                        color: isSelected ? AppTheme.textPrimary : AppTheme.textSecondary,
                                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                        fontSize: 16,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),

          // 2. Main Leanback Content Area with Overscan Margin (48dp safe padding)
          Expanded(
            child: FocusScope(
              onFocusChange: (focused) {
                if (focused && _drawerExpanded) {
                  // Collapse drawer when focus enters the content grid
                  setState(() => _drawerExpanded = false);
                }
              },
              child: Padding(
                padding: const EdgeInsets.only(left: 32, right: 48, top: 24, bottom: 24),
                child: FutureBuilder<Map<String, dynamic>>(
                  future: widget.apiService.getHomeFeed(),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }

                    final data = snapshot.data ?? {};
                    final List<MediaItem> featured = data['featured'] ?? [];
                    final List<dynamic> trays = data['trays'] ?? [];
                    final heroItem = featured.isNotEmpty ? featured.first : ApiService.localFallbackCatalog.first;

                    return SingleChildScrollView(
                      controller: _verticalScroll,
                      physics: const BouncingScrollPhysics(),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Hero Spotlight
                          HeroBanner(
                            item: heroItem,
                            isInWatchlist: widget.watchlistIds.contains(heroItem.id),
                            onPlay: () {
                              TvFocusNodeHistory.pushFocus(heroItem.id);
                              widget.onPlayMedia(heroItem);
                            },
                            onWatchlistToggle: () => widget.onToggleWatchlist(heroItem.id),
                            onDetails: () {
                              TvFocusNodeHistory.pushFocus(heroItem.id);
                              widget.onSelectMedia(heroItem);
                            },
                          ),

                          const SizedBox(height: 24),

                          // Trays with TV Focusable Cards
                          ...trays.map((tray) {
                            final List<MediaItem> items = tray['items'] ?? [];
                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Padding(
                                  padding: const EdgeInsets.symmetric(vertical: 8),
                                  child: Text(
                                    tray['title'] ?? '',
                                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppTheme.textPrimary),
                                  ),
                                ),
                                SizedBox(
                                  height: 185,
                                  child: ListView.builder(
                                    scrollDirection: Axis.horizontal,
                                    physics: const BouncingScrollPhysics(),
                                    itemCount: items.length,
                                    itemBuilder: (context, index) {
                                      final item = items[index];
                                      return Padding(
                                        padding: const EdgeInsets.only(right: 16),
                                        child: Builder(
                                          builder: (cardCtx) => TvFocusableCard(
                                            id: item.id,
                                            autofocus: index == 0 && tray == trays.first,
                                            onFocusChanged: (focused) {
                                              if (focused) {
                                                Scrollable.ensureVisible(
                                                  cardCtx,
                                                  alignment: 0.35,
                                                  duration: const Duration(milliseconds: 250),
                                                  curve: Curves.easeOutCubic,
                                                );
                                              }
                                            },
                                            onSelect: () {
                                              TvFocusNodeHistory.pushFocus(item.id);
                                              widget.onSelectMedia(item);
                                            },
                                          child: ClipRRect(
                                            borderRadius: BorderRadius.circular(AppTheme.radiusMd),
                                            child: Stack(
                                              children: [
                                                Image.network(
                                                  item.backdropUrl.isNotEmpty ? item.backdropUrl : item.posterUrl,
                                                  width: 260,
                                                  height: 155,
                                                  fit: BoxFit.cover,
                                                  errorBuilder: (c, e, s) => Container(
                                                    width: 260,
                                                    height: 155,
                                                    color: AppTheme.bgSurface2,
                                                    child: const Icon(Icons.movie, size: 48, color: AppTheme.textMuted),
                                                  ),
                                                ),
                                                Positioned(
                                                  bottom: 0,
                                                  left: 0,
                                                  right: 0,
                                                  child: Container(
                                                    padding: const EdgeInsets.all(8),
                                                    color: Colors.black.withOpacity(0.8),
                                                    child: Text(
                                                      item.title,
                                                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                                                      maxLines: 1,
                                                      overflow: TextOverflow.ellipsis,
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ),
                                      );
                                    },
                                  ),
                                ),
                                const SizedBox(height: 24),
                              ],
                            );
                          }),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
