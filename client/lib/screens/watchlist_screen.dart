import 'package:flutter/material.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import '../widgets/media_card.dart';
import '../widgets/responsive_layout.dart';

class WatchlistScreen extends StatelessWidget {
  final List<MediaItem> items;
  final Function(MediaItem) onSelectMedia;
  final VoidCallback onBrowseCatalog;

  const WatchlistScreen({
    Key? key,
    required this.items,
    required this.onSelectMedia,
    required this.onBrowseCatalog,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final isPhone = ResponsiveLayout.isPhone(context);
    final columns = isPhone ? 2 : 4;

    return Scaffold(
      backgroundColor: AppTheme.bgCanvas,
      appBar: AppBar(
        title: const Text('My Watchlist'),
      ),
      body: items.isEmpty
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.bookmark_border, size: 64, color: AppTheme.textMuted),
                  const SizedBox(height: 16),
                  const Text('Your watchlist is empty', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppTheme.textPrimary)),
                  const SizedBox(height: 8),
                  const Text('Bookmark titles while browsing to easily find them later.', style: TextStyle(color: AppTheme.textSecondary)),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: onBrowseCatalog,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.brandPrimary,
                      foregroundColor: AppTheme.bgCanvas,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    ),
                    child: const Text('Browse Featured Movies', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ],
              ),
            )
          : GridView.builder(
              padding: const EdgeInsets.all(AppTheme.space4),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: columns,
                childAspectRatio: 16 / 11,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                return MediaCard(
                  item: item,
                  aspectRatio: MediaCardAspectRatio.landscape16x9,
                  onTap: () => onSelectMedia(item),
                );
              },
            ),
    );
  }
}
