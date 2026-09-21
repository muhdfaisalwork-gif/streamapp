import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

/// ApiService - Real HTTP client for the StreamApp backend.
///
/// Primary mode: talks to the Node backend at `baseUrl`. Falls back to
/// [localFallbackCatalog] (the curated public-domain catalog) when the
/// network request fails or times out, so the Flutter client stays usable
/// even if the backend is down.
///
/// `baseUrl` is configurable at build time via:
///   flutter run --dart-define=API_BASE=http://192.168.1.5:3000
/// Defaults to localhost for emulator / desktop dev.
class ApiService {
  // Default points at the backend on the dev machine.
  // On Android emulator, use 10.0.2.2 to reach host. On physical devices,
  // pass --dart-define=API_BASE=http://<lan-ip>:3000 at build.
  final String baseUrl;

  String? _authToken;

  // Hard timeout so the UI never hangs waiting for a dead backend.
  static const _timeout = Duration(seconds: 8);

  ApiService({String? baseUrl})
      : baseUrl = baseUrl ??
            const String.fromEnvironment('API_BASE',
                defaultValue: 'http://localhost:3000');

  void setToken(String? token) {
    _authToken = token;
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_authToken != null) 'Authorization': 'Bearer $_authToken',
      };

  Future<http.Response> _get(String path) async {
    return http.get(Uri.parse('$baseUrl$path'), headers: _headers).timeout(_timeout);
  }

  Future<http.Response> _post(String path, Map<String, dynamic> body) async {
    return http
        .post(Uri.parse('$baseUrl$path'), headers: _headers, body: jsonEncode(body))
        .timeout(_timeout);
  }

  /// Static fallback for offline mode. Mirrors the LegalCatalog backend.
  /// The Flutter app still works when the backend is unreachable.
  static final List<MediaItem> localFallbackCatalog = [
    MediaItem(
      id: 'media-001',
      title: 'Sintel',
      slug: 'sintel-2010',
      description: 'A lonely young woman, Sintel, helps and befriends a dragon cub whom she calls Scales.',
      releaseYear: 2010,
      durationSeconds: 910,
      genres: ['Animation', 'Fantasy', 'Adventure'],
      posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Sintel_poster.jpg/800px-Sintel_poster.jpg',
      backdropUrl: 'https://durian.blender.org/wp-content/uploads/2010/09/sintel_desktop.png',
      rating: 'PG',
      attribution: LicenseAttribution(
        licenseType: 'CC-BY-3.0',
        creator: 'Blender Foundation & Ton Roosendaal',
        sourceUrl: 'https://durian.blender.org',
        licenseUrl: 'https://creativecommons.org/licenses/by/3.0/',
        verificationDate: '2026-09-19T00:00:00Z',
      ),
      sources: [
        StreamSource(id: 'src-001-hls', format: 'hls', url: 'https://bitdash-a.akamaihd.net/content/sintel/hls/playlist.m3u8', backupUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4', resolution: 'auto'),
        StreamSource(id: 'src-001-mp4', format: 'mp4', url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4', resolution: '1080p'),
      ],
      subtitles: [
        SubtitleTrack(id: 'sub-001-en', language: 'en', label: 'English [CC]', src: 'https://durian.blender.org/subtitles/sintel_en.vtt', isDefault: true),
      ],
      isFeatured: true,
      category: 'Blender Open Movies',
      status: 'active',
    ),
    MediaItem(
      id: 'media-002',
      title: 'Tears of Steel',
      slug: 'tears-of-steel-2012',
      description: 'Set in a dystopian future Amsterdam, warriors stage a crucial event from the past to rescue the world.',
      releaseYear: 2012,
      durationSeconds: 734,
      genres: ['Sci-Fi', 'Action', 'VFX'],
      posterUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Tears_of_Steel_poster.jpg/800px-Tears_of_Steel_poster.jpg',
      backdropUrl: 'https://mango.blender.org/wp-content/uploads/2012/09/01_thom_celia_bridge.jpg',
      rating: 'PG-13',
      attribution: LicenseAttribution(
        licenseType: 'CC-BY-3.0',
        creator: 'Blender Foundation & Ian Hubert',
        sourceUrl: 'https://mango.blender.org',
        licenseUrl: 'https://creativecommons.org/licenses/by/3.0/',
        verificationDate: '2026-09-19T00:00:00Z',
      ),
      sources: [
        StreamSource(id: 'src-002-hls', format: 'hls', url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8', resolution: 'auto'),
      ],
      subtitles: [],
      isFeatured: true,
      category: 'Blender Open Movies',
      status: 'active',
    ),
    MediaItem(
      id: 'media-005',
      title: 'Night of the Living Dead',
      slug: 'night-of-the-living-dead-1968',
      description: 'A group of survivors barricade themselves in an old farmhouse against rising corpses. George A. Romero\'s groundbreaking horror classic.',
      releaseYear: 1968,
      durationSeconds: 5760,
      genres: ['Horror', 'Classic'],
      rating: 'Not Rated',
      attribution: LicenseAttribution(
        licenseType: 'Public Domain',
        creator: 'George A. Romero',
        sourceUrl: 'https://archive.org/details/night_of_the_living_dead',
        licenseUrl: 'https://creativecommons.org/publicdomain/mark/1.0/',
        verificationDate: '2026-09-19T00:00:00Z',
      ),
      sources: [
        StreamSource(id: 'src-005-mp4', format: 'mp4', url: 'https://archive.org/download/night_of_the_living_dead/night_of_the_living_dead_512kb.mp4', resolution: '720p'),
      ],
      subtitles: [],
      isFeatured: true,
      category: 'Public Domain Classics',
      status: 'active',
    ),
  ];

  /// Fetch home feed. Falls back to local catalog on any error.
  Future<Map<String, dynamic>> getHomeFeed() async {
    try {
      // Try categories endpoint for full carousel feed
      final res = await _get('/api/v1/categories');
      if (res.statusCode == 200) {
        return jsonDecode(res.body) as Map<String, dynamic>;
      }
      throw 'Backend returned ${res.statusCode}';
    } catch (e) {
      if (kDebugMode) print('getHomeFeed network error, using fallback: $e');
      return {
        'featured': localFallbackCatalog.where((m) => m.isFeatured).toList(),
        'trays': [
          {'title': 'Blender Open Movies', 'category': 'Blender Open Movies', 'items': localFallbackCatalog.where((m) => m.category == 'Blender Open Movies').toList()},
          {'title': 'Public Domain Classics', 'category': 'Public Domain Classics', 'items': localFallbackCatalog.where((m) => m.category == 'Public Domain Classics').toList()},
        ]
      };
    }
  }

  /// Fetch all categories for the home carousels.
  Future<List<dynamic>> getCategories() async {
    try {
      final res = await _get('/api/v1/categories');
      if (res.statusCode == 200) {
        final body = jsonDecode(res.body) as Map<String, dynamic>;
        return (body['categories'] as List?) ?? [];
      }
    } catch (e) {
      if (kDebugMode) print('getCategories error: $e');
    }
    // Fallback: feed from local catalog
    return [
      {
        'id': 'featured',
        'title': 'Featured',
        'count': localFallbackCatalog.where((m) => m.isFeatured).length,
        'items': localFallbackCatalog.where((m) => m.isFeatured).toList(),
      },
      {
        'id': 'all',
        'title': 'Available Now',
        'count': localFallbackCatalog.length,
        'items': localFallbackCatalog,
      },
    ];
  }

  /// Search the backend catalog.
  Future<List<MediaItem>> search(String query, {String? type}) async {
    try {
      final params = <String, String>{};
      if (query.isNotEmpty) params['q'] = query;
      if (type != null && type != 'all') params['type'] = type;
      final qs = params.entries.map((e) => '${e.key}=${Uri.encodeQueryComponent(e.value)}').join('&');
      final res = await _get('/api/v1/search?$qs');
      if (res.statusCode == 200) {
        final body = jsonDecode(res.body) as Map<String, dynamic>;
        final results = (body['results'] as List?) ?? [];
        return results.map((j) => MediaItem.fromApiJson(j as Map<String, dynamic>)).toList();
      }
      throw 'Backend returned ${res.statusCode}';
    } catch (e) {
      if (kDebugMode) print('search error, falling back to local: $e');
      // Local fallback search
      final q = query.toLowerCase().trim();
      if (q.isEmpty) return localFallbackCatalog;
      return localFallbackCatalog.where((m) =>
        m.title.toLowerCase().contains(q) ||
        m.description.toLowerCase().contains(q) ||
        m.genres.any((g) => g.toLowerCase().contains(q))
      ).toList();
    }
  }

  /// Fetch media details.
  Future<MediaItem?> getMediaDetails(String id) async {
    try {
      // Backend doesn't have a by-id endpoint yet; query the search index
      final all = await search('');
      final hit = all.where((m) => m.id == id).toList();
      return hit.isNotEmpty ? hit.first : null;
    } catch (_) {
      try {
        return localFallbackCatalog.firstWhere((m) => m.id == id);
      } catch (_) {
        return null;
      }
    }
  }

  /// Fetch TV show episodes for a given TMDB id + season.
  Future<List<TvEpisode>> getTvEpisodes(String tmdbId, int season) async {
    try {
      final res = await _get('/api/v1/tv/$tmdbId/episodes?season=$season');
      if (res.statusCode == 200) {
        final body = jsonDecode(res.body) as Map<String, dynamic>;
        final eps = (body['episodes'] as List?) ?? [];
        return eps.map((j) => TvEpisode.fromJson(j as Map<String, dynamic>)).toList();
      }
    } catch (e) {
      if (kDebugMode) print('getTvEpisodes error: $e');
    }
    return [];
  }

  /// Resolve a working stream URL by calling the backend.
  /// Returns the chosen source's URL or null on failure.
  Future<String?> resolveStream(String mediaId, String sourceName, {int? season, int? episode}) async {
    try {
      final res = await _post('/api/v1/stream', {
        'url': mediaId,
        'sourceName': sourceName,
        if (season != null) 'season': season,
        if (episode != null) 'episode': episode,
      });
      if (res.statusCode == 200) {
        final body = jsonDecode(res.body) as Map<String, dynamic>;
        return body['streamUrl'] as String?;
      }
      if (kDebugMode) print('resolveStream failed: ${res.statusCode} ${res.body}');
      return null;
    } catch (e) {
      if (kDebugMode) print('resolveStream error: $e');
      return null;
    }
  }

  /// Send a batch of QoE telemetry events.
  Future<void> sendQoEEvents(List<Map<String, dynamic>> events, {bool optOut = false}) async {
    if (optOut || events.isEmpty) return;
    try {
      await http.post(
        Uri.parse('$baseUrl/api/v1/analytics/events'),
        headers: _headers,
        body: jsonEncode({'events': events}),
      ).timeout(_timeout);
    } catch (_) {
      // Best-effort
    }
  }

  /// Fetch active sponsor campaigns (for ethical monetization).
  Future<List<Map<String, dynamic>>> getActiveSponsors({String? mediaId}) async {
    // No backend endpoint yet - return local defaults
    return [
      {
        'id': 'sp-blender-01',
        'title': 'Blender Studio Open Movie Fund',
        'sponsorName': 'Blender Foundation',
        'message': 'Support open-source 3D animation and free creative tools at Blender Studio.',
        'ctaUrl': 'https://fund.blender.org',
        'ctaLabel': 'Support Blender Fund',
        'badgeText': 'Creator Support',
      },
      {
        'id': 'sp-archive-02',
        'title': 'Internet Archive Film Preservation',
        'sponsorName': 'Internet Archive',
        'message': 'Preserving classic cinema, cultural history, and public domain archives for the world.',
        'ctaUrl': 'https://archive.org/donate',
        'ctaLabel': 'Donate to Archive.org',
        'badgeText': 'Public Domain Preservation',
      },
    ];
  }

  Future<void> recordSponsorImpression(String campaignId) async {}
  Future<void> recordSponsorClick(String campaignId) async {}
}
