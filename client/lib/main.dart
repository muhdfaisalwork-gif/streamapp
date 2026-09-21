import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;
import 'models/models.dart';
import 'services/api_service.dart';
import 'theme/app_theme.dart';
import 'widgets/responsive_layout.dart';
import 'widgets/video_player_view.dart';
import 'screens/home_screen.dart';
import 'screens/search_screen.dart';
import 'screens/media_details_screen.dart';
import 'screens/watchlist_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/tv_detail_screen.dart';
import 'tv/tv_home_screen.dart';
import 'desktop/desktop_window_manager.dart';

void main() {
  // Desktop window setup is handled by lib/desktop/desktop_window_manager.dart.
  // Call `setupDesktopWindow()` from there if you wire it into the app.
  // Wrapping it in main() would require conditional imports that complicate
  // cross-platform compilation.
  runApp(const StreamingApp());
}

class StreamingApp extends StatefulWidget {
  const StreamingApp({Key? key}) : super(key: key);

  @override
  State<StreamingApp> createState() => _StreamingAppState();
}

class _StreamingAppState extends State<StreamingApp> {
  bool _isHighContrast = false;
  bool _telemetryEnabled = true;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StreamApp - Legal Streaming',
      debugShowCheckedModeBanner: false,
      theme: _isHighContrast ? AppTheme.highContrastTheme : AppTheme.darkTheme,
      home: AppRootShell(
        isHighContrast: _isHighContrast,
        onToggleHighContrast: (val) => setState(() => _isHighContrast = val),
        telemetryEnabled: _telemetryEnabled,
        onToggleTelemetry: (val) => setState(() => _telemetryEnabled = val),
      ),
    );
  }
}

class AppRootShell extends StatefulWidget {
  final bool isHighContrast;
  final ValueChanged<bool> onToggleHighContrast;
  final bool telemetryEnabled;
  final ValueChanged<bool> onToggleTelemetry;

  const AppRootShell({
    Key? key,
    required this.isHighContrast,
    required this.onToggleHighContrast,
    required this.telemetryEnabled,
    required this.onToggleTelemetry,
  }) : super(key: key);

  @override
  State<AppRootShell> createState() => _AppRootShellState();
}

class _AppRootShellState extends State<AppRootShell> {
  final ApiService _apiService = ApiService();
  int _selectedIndex = 0;
  final Set<String> _watchlistIds = {'media-001'};
  final Map<String, double> _continueWatchingMap = {'media-001': 45.0};
  MediaItem? _activePlayingItem;
  MediaItem? _selectedDetailItem;

  void _toggleWatchlist(String mediaId) {
    setState(() {
      if (_watchlistIds.contains(mediaId)) {
        _watchlistIds.remove(mediaId);
      } else {
        _watchlistIds.add(mediaId);
      }
    });
  }

  void _onPlayMedia(MediaItem item) {
    setState(() {
      _activePlayingItem = item;
      _selectedDetailItem = null;
    });
  }

  void _onSelectMedia(MediaItem item) {
    setState(() {
      _selectedDetailItem = item;
    });
  }

  void _onBookmarkUpdate(String mediaId, double pos, double dur) {
    setState(() {
      final pct = (pos / dur) * 100.0;
      _continueWatchingMap[mediaId] = pct;
    });
  }

  @override
  Widget build(BuildContext context) {
    // 1. Fullscreen Video Player Mode
    if (_activePlayingItem != null) {
      final source = _activePlayingItem!.sources.isNotEmpty
          ? _activePlayingItem!.sources.first
          : StreamSource(id: 'default', format: 'hls', url: '', resolution: 'auto');

      return VideoPlayerView(
        item: _activePlayingItem!,
        initialSource: source,
        onBack: () => setState(() => _activePlayingItem = null),
        onProgressUpdate: (pos, dur) => _onBookmarkUpdate(_activePlayingItem!.id, pos, dur),
      );
    }

    // 2. Title Details Modal Page
    if (_selectedDetailItem != null) {
      return MediaDetailsScreen(
        item: _selectedDetailItem!,
        isInWatchlist: _watchlistIds.contains(_selectedDetailItem!.id),
        resumePercentage: _continueWatchingMap[_selectedDetailItem!.id],
        onPlay: () => _onPlayMedia(_selectedDetailItem!),
        onToggleWatchlist: () => _toggleWatchlist(_selectedDetailItem!.id),
      );
    }

    final isPhone = ResponsiveLayout.isPhone(context);

    // 3. Screen Switcher
    Widget currentScreen;
    switch (_selectedIndex) {
      case 0:
        currentScreen = HomeScreen(
          apiService: _apiService,
          onPlayMedia: _onPlayMedia,
          onSelectMedia: _onSelectMedia,
          watchlistIds: _watchlistIds,
          onToggleWatchlist: _toggleWatchlist,
          continueWatchingMap: _continueWatchingMap,
        );
        break;
      case 1:
        currentScreen = SearchScreen(
          apiService: _apiService,
          onSelectMedia: _onSelectMedia,
        );
        break;
      case 2:
        final watchlistItems = ApiService.localFallbackCatalog
            .where((m) => _watchlistIds.contains(m.id))
            .toList();
        currentScreen = WatchlistScreen(
          items: watchlistItems,
          onSelectMedia: _onSelectMedia,
          onBrowseCatalog: () => setState(() => _selectedIndex = 0),
        );
        break;
      case 3:
      default:
        currentScreen = SettingsScreen(
          isHighContrast: widget.isHighContrast,
          onToggleHighContrast: widget.onToggleHighContrast,
          telemetryEnabled: widget.telemetryEnabled,
          onToggleTelemetry: widget.onToggleTelemetry,
        );
        break;
    }

    // 4. Responsive Shell: BottomNav for Phone vs NavigationRail for Tablet/Desktop
    if (isPhone) {
      return Scaffold(
        body: SafeArea(child: currentScreen),
        bottomNavigationBar: BottomNavigationBar(
          currentIndex: _selectedIndex,
          onTap: (idx) => setState(() => _selectedIndex = idx),
          items: const [
            BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
            BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
            BottomNavigationBarItem(icon: Icon(Icons.bookmark), label: 'Watchlist'),
            BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
          ],
        ),
      );
    } else {
      return Scaffold(
        body: Row(
          children: [
            NavigationRail(
              selectedIndex: _selectedIndex,
              onDestinationSelected: (idx) => setState(() => _selectedIndex = idx),
              backgroundColor: AppTheme.bgSurface1,
              selectedIconTheme: const IconThemeData(color: AppTheme.brandPrimary),
              unselectedIconTheme: const IconThemeData(color: AppTheme.textMuted),
              labelType: NavigationRailLabelType.all,
              leading: const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Icon(Icons.play_circle_fill, size: 36, color: AppTheme.brandPrimary),
              ),
              destinations: const [
                NavigationRailDestination(icon: Icon(Icons.home), label: Text('Home')),
                NavigationRailDestination(icon: Icon(Icons.search), label: Text('Search')),
                NavigationRailDestination(icon: Icon(Icons.bookmark), label: Text('Watchlist')),
                NavigationRailDestination(icon: Icon(Icons.settings), label: Text('Settings')),
              ],
            ),
            const VerticalDivider(width: 1, color: AppTheme.bgSurface3),
            Expanded(child: currentScreen),
          ],
        ),
      );
    }
  }
}
