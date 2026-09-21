import { Database } from '../db/database.ts';

export interface StreamHealthResult {
  mediaId: string;
  title: string;
  sourceId: string;
  url: string;
  isReachable: boolean;
  httpStatus?: number;
  latencyMs: number;
}

export class HealthService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  async probeUrl(url: string, timeoutMs = 3000): Promise<{ reachable: boolean; status?: number; latencyMs: number }> {
    const start = Date.now();
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), timeoutMs);

      // Perform HEAD or Range GET request
      const response = await fetch(url, {
        method: 'HEAD',
        signal: controller.signal,
        headers: { 'User-Agent': 'StreamingApp-HealthMonitor/1.0' }
      });
      clearTimeout(timeout);
      const latencyMs = Date.now() - start;

      return {
        reachable: response.ok || response.status === 206 || response.status === 302 || response.status === 403, // CDN sometimes returns 403 to HEAD but works for GET
        status: response.status,
        latencyMs
      };
    } catch {
      return {
        reachable: false,
        latencyMs: Date.now() - start
      };
    }
  }

  async runHealthCheckAll(): Promise<StreamHealthResult[]> {
    const media = this.db.getAllMedia();
    const results: StreamHealthResult[] = [];

    for (const item of media) {
      for (const source of item.sources) {
        // Probe stream
        const probe = await this.probeUrl(source.url);
        results.push({
          mediaId: item.id,
          title: item.title,
          sourceId: source.id,
          url: source.url,
          isReachable: probe.reachable,
          httpStatus: probe.status,
          latencyMs: probe.latencyMs
        });

        // If primary is down, mark media as degraded
        if (!probe.reachable && source === item.sources[0]) {
          this.db.updateMediaStatus(item.id, 'degraded');
        }
      }
    }

    return results;
  }

  getSystemStatus(): {
    status: 'healthy' | 'degraded';
    mediaCount: number;
    activeCount: number;
    degradedCount: number;
    quarantinedCount: number;
    timestamp: string;
  } {
    const all = this.db.getAllMedia(true);
    const active = all.filter(m => m.status === 'active').length;
    const degraded = all.filter(m => m.status === 'degraded').length;
    const quarantined = all.filter(m => m.status === 'suspended_pending_review').length;

    return {
      status: degraded > 0 ? 'degraded' : 'healthy',
      mediaCount: all.length,
      activeCount: active,
      degradedCount: degraded,
      quarantinedCount: quarantined,
      timestamp: new Date().toISOString()
    };
  }
}
