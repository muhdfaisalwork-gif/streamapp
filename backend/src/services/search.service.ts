import { Database } from '../db/database.ts';
import type { MediaItem } from '../types/index.ts';

export interface SearchOptions {
  query?: string;
  genre?: string;
  category?: string;
  year?: number;
}

export class SearchService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  search(options: SearchOptions): {
    total: number;
    results: MediaItem[];
    genresMatched: string[];
  } {
    const all = this.db.getAllMedia();
    const q = options.query ? options.query.toLowerCase().trim() : '';

    const results = all.filter(item => {
      // Exclude quarantined items
      if (item.status === 'suspended_pending_review') return false;

      // Filter by genre
      if (options.genre && !item.genres.some(g => g.toLowerCase() === options.genre!.toLowerCase())) {
        return false;
      }

      // Filter by category
      if (options.category && item.category.toLowerCase() !== options.category.toLowerCase()) {
        return false;
      }

      // Filter by year
      if (options.year && item.releaseYear !== options.year) {
        return false;
      }

      // Filter by query string
      if (q) {
        const titleMatch = item.title.toLowerCase().includes(q);
        const descMatch = item.description.toLowerCase().includes(q);
        const creatorMatch = item.attribution.creator.toLowerCase().includes(q);
        const genreMatch = item.genres.some(g => g.toLowerCase().includes(q));
        return titleMatch || descMatch || creatorMatch || genreMatch;
      }

      return true;
    });

    const genresMatched = Array.from(
      new Set(results.flatMap(r => r.genres))
    ).sort();

    return {
      total: results.length,
      results,
      genresMatched
    };
  }
}
