class LicenseAttribution {
  final String licenseType;
  final String creator;
  final String sourceUrl;
  final String licenseUrl;
  final String verificationDate;

  LicenseAttribution({
    required this.licenseType,
    required this.creator,
    required this.sourceUrl,
    required this.licenseUrl,
    required this.verificationDate,
  });

  factory LicenseAttribution.fromJson(Map<String, dynamic> json) {
    return LicenseAttribution(
      licenseType: json['licenseType'] ?? 'Public Domain',
      creator: json['creator'] ?? 'Unknown',
      sourceUrl: json['sourceUrl'] ?? '',
      licenseUrl: json['licenseUrl'] ?? '',
      verificationDate: json['verificationDate'] ?? '',
    );
  }
}

class SubtitleTrack {
  final String id;
  final String language;
  final String label;
  final String src;
  final bool isDefault;

  SubtitleTrack({
    required this.id,
    required this.language,
    required this.label,
    required this.src,
    required this.isDefault,
  });

  factory SubtitleTrack.fromJson(Map<String, dynamic> json) {
    return SubtitleTrack(
      id: json['id'] ?? '',
      language: json['language'] ?? 'en',
      label: json['label'] ?? 'English',
      src: json['src'] ?? '',
      isDefault: json['isDefault'] ?? false,
    );
  }
}

class StreamSource {
  final String id;
  final String format; // 'hls', 'dash', 'mp4', 'embed', 'torrent'
  final String url;
  final String? backupUrl;
  final String resolution;
  final int? bitrateBps;
  final String? label;
  final String? provider;
  final String? urlTemplate; // for TV sources with {season}/{episode}
  final bool seasonEpisode;

  StreamSource({
    required this.id,
    required this.format,
    required this.url,
    this.backupUrl,
    required this.resolution,
    this.bitrateBps,
    this.label,
    this.provider,
    this.urlTemplate,
    this.seasonEpisode = false,
  });

  factory StreamSource.fromJson(Map<String, dynamic> json) {
    return StreamSource(
      id: json['id'] ?? '',
      format: json['format'] ?? 'hls',
      url: json['url'] ?? '',
      backupUrl: json['backupUrl'],
      resolution: json['resolution'] ?? 'auto',
      bitrateBps: json['bitrateBps'],
      label: json['label'],
      provider: json['provider'],
      urlTemplate: json['urlTemplate'],
      seasonEpisode: json['seasonEpisode'] ?? false,
    );
  }
}

class MediaItem {
  final String id;
  final String title;
  final String slug;
  final String description;
  final int releaseYear;
  final int durationSeconds;
  final List<String> genres;
  final String posterUrl;
  final String backdropUrl;
  final String rating;
  final LicenseAttribution attribution;
  final List<StreamSource> sources;
  final List<SubtitleTrack> subtitles;
  final bool isFeatured;
  final String category;
  final String status;

  // New fields for the unified backend catalog
  final String type;          // 'movie' | 'tv'
  final String? imdbId;
  final String? tmdbId;
  final int? seasons;         // TV only
  final String sourceName;     // which scraper/source this came from

  MediaItem({
    required this.id,
    required this.title,
    required this.slug,
    required this.description,
    required this.releaseYear,
    required this.durationSeconds,
    required this.genres,
    required this.posterUrl,
    required this.backdropUrl,
    required this.rating,
    required this.attribution,
    required this.sources,
    required this.subtitles,
    required this.isFeatured,
    required this.category,
    required this.status,
    this.type = 'movie',
    this.imdbId,
    this.tmdbId,
    this.seasons,
    this.sourceName = 'MovieBox',
  });

  factory MediaItem.fromJson(Map<String, dynamic> json) {
    return MediaItem(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      slug: json['slug'] ?? '',
      description: json['description'] ?? '',
      releaseYear: json['releaseYear'] ?? 2026,
      durationSeconds: json['durationSeconds'] ?? 0,
      genres: (json['genres'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      posterUrl: json['posterUrl'] ?? '',
      backdropUrl: json['backdropUrl'] ?? '',
      rating: json['rating'] ?? 'NR',
      attribution: LicenseAttribution.fromJson(json['attribution'] ?? const {}),
      sources: (json['sources'] as List<dynamic>?)?.map((e) => StreamSource.fromJson(e)).toList() ?? [],
      subtitles: (json['subtitles'] as List<dynamic>?)?.map((e) => SubtitleTrack.fromJson(e)).toList() ?? [],
      isFeatured: json['isFeatured'] ?? false,
      category: json['category'] ?? 'General',
      status: json['status'] ?? 'active',
    );
  }

  /// Parse the backend API JSON shape (MovieBoxScraper toFrontendItem).
  factory MediaItem.fromApiJson(Map<String, dynamic> json) {
    final sources = (json['streams'] as List<dynamic>?) ?? [];
    return MediaItem(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      slug: json['id'] ?? '',
      description: json['description'] ?? '',
      releaseYear: json['year'] ?? 0,
      durationSeconds: json['duration'] ?? 0,
      genres: (json['genres'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      posterUrl: json['poster'] ?? '',
      backdropUrl: json['backdrop'] ?? '',
      rating: json['rating']?.toString() ?? 'NR',
      attribution: LicenseAttribution(
        licenseType: json['license']?.toString() ?? 'Aggregator',
        creator: json['creator']?.toString() ?? 'Various',
        sourceUrl: '',
        licenseUrl: '',
        verificationDate: '',
      ),
      sources: sources.map((s) => StreamSource.fromJson(s as Map<String, dynamic>)).toList(),
      subtitles: [],
      isFeatured: false,
      category: 'Catalog',
      status: 'active',
      type: json['type'] ?? 'movie',
      imdbId: json['imdbId'],
      tmdbId: json['tmdbId']?.toString(),
      seasons: json['seasons'],
      sourceName: json['sourceName'] ?? 'MovieBox',
    );
  }
}

class TvEpisode {
  final int season;
  final int episode;
  final String title;
  final String? overview;
  final int? runtime;
  final List<StreamSource> sources;

  TvEpisode({
    required this.season,
    required this.episode,
    required this.title,
    this.overview,
    this.runtime,
    required this.sources,
  });

  factory TvEpisode.fromJson(Map<String, dynamic> json) {
    return TvEpisode(
      season: json['season'] ?? 1,
      episode: json['episode'] ?? 1,
      title: json['title'] ?? 'Episode ${json['episode']}',
      overview: json['overview'],
      runtime: json['runtime'],
      sources: (json['sources'] as List<dynamic>?)
              ?.map((s) => StreamSource.fromJson(s as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class PlaybackBookmark {
  final String userId;
  final String mediaId;
  final double positionSeconds;
  final double durationSeconds;
  final double completedPercentage;
  final String updatedAt;

  PlaybackBookmark({
    required this.userId,
    required this.mediaId,
    required this.positionSeconds,
    required this.durationSeconds,
    required this.completedPercentage,
    required this.updatedAt,
  });

  factory PlaybackBookmark.fromJson(Map<String, dynamic> json) {
    return PlaybackBookmark(
      userId: json['userId'] ?? 'guest',
      mediaId: json['mediaId'] ?? '',
      positionSeconds: (json['positionSeconds'] as num?)?.toDouble() ?? 0.0,
      durationSeconds: (json['durationSeconds'] as num?)?.toDouble() ?? 0.0,
      completedPercentage: (json['completedPercentage'] as num?)?.toDouble() ?? 0.0,
      updatedAt: json['updatedAt'] ?? '',
    );
  }
}

class User {
  final String id;
  final String email;
  final String displayName;
  final String role;

  User({
    required this.id,
    required this.email,
    required this.displayName,
    required this.role,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? '',
      email: json['email'] ?? '',
      displayName: json['displayName'] ?? '',
      role: json['role'] ?? 'user',
    );
  }
}
