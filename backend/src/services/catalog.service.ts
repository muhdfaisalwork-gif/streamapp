import { Database } from '../db/database.ts';
import type { MediaItem } from '../types/index.ts';

export class CatalogService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  getHomeFeed(): {
    featured: MediaItem[];
    trays: { title: string; category: string; items: MediaItem[] }[];
  } {
    const all = this.db.getAllMedia();
    const featured = all.filter(m => m.isFeatured);

    // Group remaining into trays by category
    const categoryMap = new Map<string, MediaItem[]>();
    for (const item of all) {
      const cat = item.category || 'General';
      if (!categoryMap.has(cat)) {
        categoryMap.set(cat, []);
      }
      categoryMap.get(cat)!.push(item);
    }

    const trays = Array.from(categoryMap.entries()).map(([category, items]) => ({
      title: category,
      category,
      items
    }));

    return {
      featured: featured.length > 0 ? featured : all.slice(0, 2),
      trays
    };
  }

  getItemById(id: string): MediaItem | null {
    return this.db.getMediaById(id);
  }

  getGenres(): string[] {
    const all = this.db.getAllMedia();
    const set = new Set<string>();
    for (const item of all) {
      for (const g of item.genres) {
        set.add(g);
      }
    }
    return Array.from(set).sort();
  }
}
