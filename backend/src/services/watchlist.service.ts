import { Database } from '../db/database.ts';
import type { MediaItem } from '../types/index.ts';

export class WatchlistService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  addToWatchlist(userId: string, mediaId: string): void {
    const item = this.db.getMediaById(mediaId);
    if (!item) {
      throw new Error(`Media not found: ${mediaId}`);
    }
    this.db.addToWatchlist(userId, mediaId);
  }

  removeFromWatchlist(userId: string, mediaId: string): void {
    this.db.removeFromWatchlist(userId, mediaId);
  }

  getWatchlist(userId: string): MediaItem[] {
    const ids = this.db.getWatchlist(userId);
    const items: MediaItem[] = [];
    for (const id of ids) {
      const item = this.db.getMediaById(id);
      if (item && item.status !== 'suspended_pending_review') {
        items.push(item);
      }
    }
    return items;
  }
}
