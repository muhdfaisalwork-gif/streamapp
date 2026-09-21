import { Database } from '../db/database.ts';
import type { DmcaTakedownNotice } from '../types/index.ts';
import { CryptoUtil } from '../utils/crypto.ts';

export class LegalService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  submitTakedownNotice(data: {
    mediaId: string;
    claimantName: string;
    claimantEmail: string;
    copyrightWorkDescription: string;
    statementOfGoodFaith: boolean;
    digitalSignature: string;
  }): { notice: DmcaTakedownNotice; actionTaken: string } {
    if (!data.mediaId || !data.claimantEmail || !data.digitalSignature) {
      throw new Error('Missing required DMCA takedown fields');
    }

    if (!data.statementOfGoodFaith) {
      throw new Error('A statement of good faith belief is legally required for DMCA notices');
    }

    const notice: DmcaTakedownNotice = {
      id: CryptoUtil.randomId('dmca'),
      mediaId: data.mediaId,
      claimantName: data.claimantName,
      claimantEmail: data.claimantEmail,
      copyrightWorkDescription: data.copyrightWorkDescription,
      statementOfGoodFaith: data.statementOfGoodFaith,
      digitalSignature: data.digitalSignature,
      status: 'quarantined',
      submittedAt: new Date().toISOString()
    };

    // Save notice
    this.db.createDmcaNotice(notice);

    // INSTANT QUARANTINE (<60s SLA): Immediately hide disputed media from catalog and playback
    const changed = this.db.updateMediaStatus(data.mediaId, 'suspended_pending_review');

    return {
      notice,
      actionTaken: changed 
        ? `Media ID ${data.mediaId} has been immediately quarantined and removed from public streaming pending legal review.`
        : `Media ID ${data.mediaId} not found in catalog, but notice was formally logged.`
    };
  }

  getAuditLog(): DmcaTakedownNotice[] {
    return this.db.getDmcaNotices();
  }
}
