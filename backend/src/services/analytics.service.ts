import { Database } from '../db/database.ts';
import type { QoEEvent, SponsorCampaign } from '../types/index.ts';
import { CryptoUtil } from '../utils/crypto.ts';

export class AnalyticsService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  recordEvent(event: Omit<QoEEvent, 'id' | 'timestamp'>, consentOptOut = false): { event?: QoEEvent; optedOut: boolean } {
    if (consentOptOut) {
      return { optedOut: true };
    }

    const fullEvent: QoEEvent = {
      ...event,
      id: CryptoUtil.randomId('qoe'),
      timestamp: new Date().toISOString()
    };

    this.db.recordQoEEvent(fullEvent);
    return { event: fullEvent, optedOut: false };
  }

  recordBatchEvents(
    events: Array<Omit<QoEEvent, 'id' | 'timestamp'>>,
    consentOptOut = false
  ): { ingested: number; optedOut: boolean } {
    if (consentOptOut || !Array.isArray(events) || events.length === 0) {
      return { ingested: 0, optedOut: consentOptOut };
    }

    const now = new Date().toISOString();
    const fullEvents: QoEEvent[] = events.map(e => ({
      ...e,
      id: CryptoUtil.randomId('qoe'),
      timestamp: now
    }));

    this.db.recordQoEEvents(fullEvents);
    return { ingested: fullEvents.length, optedOut: false };
  }

  getDashboardMetrics(): {
    totalEvents: number;
    averageStartupMs: number;
    totalBufferStalls: number;
    healthStatus: string;
  } {
    const stats = this.db.getQoEStats();
    return {
      ...stats,
      healthStatus: stats.totalBufferStalls > 20 ? 'Action Required' : 'Excellent'
    };
  }

  getActiveSponsors(mediaId?: string): SponsorCampaign[] {
    return this.db.getActiveSponsors(mediaId);
  }

  recordSponsorImpression(campaignId: string): boolean {
    return this.db.recordSponsorImpression(campaignId);
  }

  recordSponsorClick(campaignId: string): boolean {
    return this.db.recordSponsorClick(campaignId);
  }
}

