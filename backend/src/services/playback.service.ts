import { Database } from '../db/database.ts';
import type { MediaItem, StreamSource, SubtitleTrack, PlaybackBookmark } from '../types/index.ts';

export class PlaybackService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  resolveStream(mediaId: string, preferredFormat: 'hls' | 'dash' | 'mp4' = 'hls'): {
    mediaId: string;
    title: string;
    activeSource: StreamSource;
    fallbackSource?: StreamSource;
    availableSources: StreamSource[];
    subtitles: SubtitleTrack[];
    attribution: MediaItem['attribution'];
  } {
    const item = this.db.getMediaById(mediaId);
    if (!item) {
      throw new Error(`Media not found: ${mediaId}`);
    }

    if (item.status === 'suspended_pending_review') {
      throw new Error('This title is temporarily unavailable due to review');
    }

    if (!item.sources || item.sources.length === 0) {
      throw new Error('No stream sources available for this title');
    }

    // Attempt to match preferred format, otherwise fallback to first available
    let activeSource = item.sources.find(s => s.format === preferredFormat);
    if (!activeSource) {
      activeSource = item.sources[0];
    }

    // Find fallback source (e.g. mp4 if active is hls, or second stream)
    const fallbackSource = item.sources.find(s => s.id !== activeSource!.id) || (activeSource.backupUrl ? {
      id: `${activeSource.id}-backup`,
      format: 'mp4',
      url: activeSource.backupUrl,
      resolution: '720p',
      isHealthVerified: true
    } as StreamSource : undefined);

    return {
      mediaId: item.id,
      title: item.title,
      activeSource,
      fallbackSource,
      availableSources: item.sources,
      subtitles: item.subtitles,
      attribution: item.attribution
    };
  }

  saveBookmark(userId: string, mediaId: string, positionSeconds: number, durationSeconds: number): PlaybackBookmark {
    const validDuration = Math.max(0, durationSeconds);
    const clampedPos = Math.max(0, validDuration > 0 ? Math.min(positionSeconds, validDuration) : positionSeconds);
    const completedPercentage = validDuration > 0 
      ? Math.min(100, Math.round((clampedPos / validDuration) * 100))
      : 0;

    const bookmark: PlaybackBookmark = {
      userId,
      mediaId,
      positionSeconds: clampedPos,
      durationSeconds: validDuration,
      completedPercentage,
      updatedAt: new Date().toISOString()
    };

    this.db.saveBookmark(bookmark);
    return bookmark;
  }

  getBookmark(userId: string, mediaId: string): PlaybackBookmark | null {
    return this.db.getBookmark(userId, mediaId);
  }

  getContinueWatching(userId: string): { media: MediaItem; bookmark: PlaybackBookmark }[] {
    const bookmarks = this.db.getBookmarksByUser(userId);
    const results: { media: MediaItem; bookmark: PlaybackBookmark }[] = [];

    for (const b of bookmarks) {
      // Exclude titles that are > 95% complete or < 10 seconds in
      if (b.completedPercentage < 95 && b.positionSeconds > 10) {
        const item = this.db.getMediaById(b.mediaId);
        if (item && item.status !== 'suspended_pending_review') {
          results.push({ media: item, bookmark: b });
        }
      }
    }

    return results;
  }
}
