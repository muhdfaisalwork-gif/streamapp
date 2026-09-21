export type LicenseType = 
  | 'Public Domain' 
  | 'CC-BY-3.0' 
  | 'CC-BY-4.0' 
  | 'CC-BY-SA-4.0' 
  | 'CC0'
  | 'Official Educational';

export interface LicenseAttribution {
  licenseType: LicenseType;
  creator: string;
  sourceUrl: string;
  licenseUrl: string;
  verificationDate: string; // ISO 8601
}

export interface SubtitleTrack {
  id: string;
  language: string; // e.g. 'en', 'es', 'fr', 'de'
  label: string;
  src: string; // WebVTT URL
  isDefault: boolean;
}

export interface StreamSource {
  id: string;
  format: 'hls' | 'dash' | 'mp4';
  url: string;
  backupUrl?: string;
  resolution: '4K' | '1080p' | '720p' | '480p' | 'auto';
  bitrateBps?: number;
  fps?: number;
  isHealthVerified?: boolean;
}

export interface MediaItem {
  id: string;
  title: string;
  slug: string;
  description: string;
  releaseYear: number;
  durationSeconds: number;
  genres: string[];
  posterUrl: string;
  backdropUrl: string;
  rating: string;
  attribution: LicenseAttribution;
  sources: StreamSource[];
  subtitles: SubtitleTrack[];
  isFeatured: boolean;
  category: string; // e.g. 'Featured', 'Blender Open Movies', 'Public Domain Classics', 'NASA & Science'
  status: 'active' | 'degraded' | 'suspended_pending_review';
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  email: string;
  passwordHash: string;
  displayName: string;
  role: 'user' | 'admin';
  createdAt: string;
  updatedAt: string;
}

export interface PlaybackBookmark {
  userId: string; // or 'guest'
  mediaId: string;
  positionSeconds: number;
  durationSeconds: number;
  completedPercentage: number;
  updatedAt: string;
}

export interface WatchlistEntry {
  userId: string;
  mediaId: string;
  addedAt: string;
}

export interface DmcaTakedownNotice {
  id: string;
  mediaId: string;
  claimantName: string;
  claimantEmail: string;
  copyrightWorkDescription: string;
  statementOfGoodFaith: boolean;
  digitalSignature: string;
  status: 'pending' | 'quarantined' | 'dismissed' | 'resolved';
  submittedAt: string;
}

export interface QoEEvent {
  id: string;
  sessionId: string;
  mediaId: string;
  platform: 'android-phone' | 'android-tablet' | 'android-tv' | 'windows' | 'linux';
  eventType: 'start' | 'buffer_stall' | 'bitrate_shift' | 'error' | 'complete';
  startupTimeMs?: number;
  bufferDurationMs?: number;
  targetBitrateBps?: number;
  errorCode?: string;
  timestamp: string;
}

export interface SponsorCampaign {
  id: string;
  title: string;
  sponsorName: string;
  message: string;
  ctaUrl: string;
  ctaLabel: string;
  badgeText: string;
  mediaId?: string | null;
  impressions: number;
  clicks: number;
  status: 'active' | 'paused' | 'archived';
  createdAt: string;
}

