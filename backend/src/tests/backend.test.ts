import { test, describe, before, after } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { StreamingServer } from '../server.ts';

const TEST_DB = path.resolve(process.cwd(), 'test_streaming.db');
const TEST_PORT = 4099;
const BASE_URL = `http://localhost:${TEST_PORT}`;

describe('Cross-Platform Legal Streaming App - Backend Test Suite', () => {
  let server: StreamingServer;

  before(async () => {
    if (fs.existsSync(TEST_DB)) {
      fs.unlinkSync(TEST_DB);
    }
    server = new StreamingServer(TEST_DB);
    await server.listen(TEST_PORT, 'localhost');
  });

  after(async () => {
    await server.close();
    if (fs.existsSync(TEST_DB)) {
      try { fs.unlinkSync(TEST_DB); } catch {}
    }
  });

  test('1. Health Check Endpoint returns healthy status with media counts', async () => {
    const res = await fetch(`${BASE_URL}/health`);
    assert.strictEqual(res.status, 200);
    const body = await res.json();
    assert.strictEqual(body.status, 'healthy');
    assert.ok(body.mediaCount >= 7, 'Seed catalog should have at least 7 verified legal titles');
    assert.strictEqual(body.quarantinedCount, 0);
  });

  test('2. Catalog Home Feed returns Hero carousel and category Trays', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/catalog/home`);
    assert.strictEqual(res.status, 200);
    const body = await res.json();
    assert.strictEqual(body.success, true);
    assert.ok(body.data.featured.length > 0, 'Should have featured hero items');
    assert.ok(body.data.trays.length >= 3, 'Should have multiple category trays');
    
    // Check legal attribution on first item
    const first = body.data.featured[0];
    assert.ok(first.attribution.licenseType, 'Must have legal license attribution');
    assert.ok(first.attribution.creator, 'Must have creator attribution');
  });

  test('3. Media Details endpoint returns complete media metadata', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/catalog/media/media-001`);
    assert.strictEqual(res.status, 200);
    const body = await res.json();
    assert.strictEqual(body.success, true);
    assert.strictEqual(body.data.title, 'Sintel');
    assert.strictEqual(body.data.attribution.licenseType, 'CC-BY-3.0');
    assert.ok(body.data.sources.length >= 2, 'Should provide both HLS and MP4 fallback sources');
  });

  test('4. Search Engine filters accurately by query string', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/search?q=sintel`);
    assert.strictEqual(res.status, 200);
    const body = await res.json();
    assert.strictEqual(body.success, true);
    assert.ok(body.data.total >= 1);
    assert.strictEqual(body.data.results[0].title, 'Sintel');
  });

  test('5. Auth Engine handles Registration, Password Verification & JWT Session', async () => {
    // Register
    const regRes = await fetch(`${BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'alex.viewer@example.com',
        password: 'securePassword123!',
        displayName: 'Alex Viewer'
      })
    });
    assert.strictEqual(regRes.status, 201);
    const regBody = await regRes.json();
    assert.strictEqual(regBody.success, true);
    assert.ok(regBody.data.token, 'Should return JWT token');
    const token = regBody.data.token;

    // Verify /auth/me with Bearer token
    const meRes = await fetch(`${BASE_URL}/api/v1/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    assert.strictEqual(meRes.status, 200);
    const meBody = await meRes.json();
    assert.strictEqual(meBody.data.email, 'alex.viewer@example.com');

    // Login with invalid password fails
    const badLogin = await fetch(`${BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'alex.viewer@example.com', password: 'wrongPassword' })
    });
    assert.strictEqual(badLogin.status, 400);

    // Login with valid password succeeds
    const goodLogin = await fetch(`${BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'alex.viewer@example.com', password: 'securePassword123!' })
    });
    assert.strictEqual(goodLogin.status, 200);
  });

  test('6. Guest-to-User Sync reconciles bookmarks and watchlist', async () => {
    // Register secondary user
    const reg = await (await fetch(`${BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'sync.test@example.com', password: 'password123', displayName: 'Sync User' })
    })).json();
    const token = reg.data.token;

    // Push local guest bookmarks and watchlist
    const syncRes = await fetch(`${BASE_URL}/api/v1/auth/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        bookmarks: [{ mediaId: 'media-001', positionSeconds: 320, durationSeconds: 910 }],
        watchlist: ['media-002', 'media-003']
      })
    });
    assert.strictEqual(syncRes.status, 200);
    const syncBody = await syncRes.json();
    assert.strictEqual(syncBody.data.syncedBookmarks, 1);
    assert.strictEqual(syncBody.data.syncedWatchlist, 2);

    // Verify Continue Watching reflects synced bookmark
    const cwRes = await fetch(`${BASE_URL}/api/v1/playback/continue-watching`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const cwBody = await cwRes.json();
    assert.strictEqual(cwBody.data.length, 1);
    assert.strictEqual(cwBody.data[0].media.id, 'media-001');
    assert.strictEqual(cwBody.data[0].bookmark.positionSeconds, 320);
  });

  test('7. Stream Resolution provides primary and secondary fallback sources', async () => {
    const res = await fetch(`${BASE_URL}/api/v1/playback/resolve/media-001?format=hls`);
    assert.strictEqual(res.status, 200);
    const body = await res.json();
    assert.strictEqual(body.success, true);
    assert.strictEqual(body.data.activeSource.format, 'hls');
    assert.ok(body.data.fallbackSource, 'Must include fallback source for playback recovery');
    assert.ok(body.data.activeSource.url.length > 0);

    // Verify 404 on missing media
    const missingRes = await fetch(`${BASE_URL}/api/v1/playback/resolve/media-non-existent`);
    assert.strictEqual(missingRes.status, 404);

    // Verify rejection of empty mediaId
    const emptyWatchlist = await fetch(`${BASE_URL}/api/v1/watchlist/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    assert.strictEqual(emptyWatchlist.status, 400);
  });

  test('8. DMCA Takedown and Automated Instant Quarantine (<60s SLA)', async () => {
    // Media-006 is Metropolis
    const beforeCheck = await (await fetch(`${BASE_URL}/api/v1/catalog/media/media-006`)).json();
    assert.strictEqual(beforeCheck.success, true);

    // Submit DMCA notice
    const takedownRes = await fetch(`${BASE_URL}/api/v1/legal/takedown`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mediaId: 'media-006',
        claimantName: 'Test Representative',
        claimantEmail: 'legal.test@example.com',
        copyrightWorkDescription: 'Disputed distribution rights inquiry',
        statementOfGoodFaith: true,
        digitalSignature: 'Test Rep 2026'
      })
    });
    assert.strictEqual(takedownRes.status, 201);

    // Verify title is IMMEDIATELY quarantined and blocked from playback
    const playbackRes = await fetch(`${BASE_URL}/api/v1/playback/resolve/media-006`);
    assert.strictEqual(playbackRes.status, 400); // Throws error: temporarily unavailable due to review

    // Verify title is removed from public catalog feed
    const feedRes = await (await fetch(`${BASE_URL}/api/v1/catalog/home`)).json();
    const foundInFeed = feedRes.data.trays.some((t: any) => t.items.some((i: any) => i.id === 'media-006'));
    assert.strictEqual(foundInFeed, false, 'Quarantined title must not appear in any public catalog tray');

    // Verify Audit Log records notice
    const auditRes = await (await fetch(`${BASE_URL}/api/v1/legal/audit`)).json();
    assert.ok(auditRes.data.length >= 1);
    assert.strictEqual(auditRes.data[0].mediaId, 'media-006');
    assert.strictEqual(auditRes.data[0].status, 'quarantined');
  });

  test('9. QoE Telemetry records metrics and aggregates dashboard stats', async () => {
    const qoeRes = await fetch(`${BASE_URL}/api/v1/analytics/qoe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId: 'sess-test-123',
        mediaId: 'media-001',
        platform: 'android-tv',
        eventType: 'start',
        startupTimeMs: 840
      })
    });
    assert.strictEqual(qoeRes.status, 201);

    const dashRes = await (await fetch(`${BASE_URL}/api/v1/analytics/dashboard`)).json();
    assert.strictEqual(dashRes.success, true);
    assert.ok(dashRes.data.totalEvents >= 1);
    assert.ok(dashRes.data.averageStartupMs > 0);
  });

  test('10. Batch QoE ingestion and Privacy Opt-Out (GDPR/DNT compliance)', async () => {
    // A. Batch ingestion with consent
    const batchRes = await fetch(`${BASE_URL}/api/v1/analytics/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        events: [
          {
            sessionId: 'sess-batch-001',
            mediaId: 'media-002',
            platform: 'windows',
            eventType: 'start',
            startupTimeMs: 450
          },
          {
            sessionId: 'sess-batch-001',
            mediaId: 'media-002',
            platform: 'windows',
            eventType: 'bitrate_shift',
            targetBitrateBps: 8000000
          }
        ]
      })
    });
    assert.strictEqual(batchRes.status, 200);
    const batchData = await batchRes.json();
    assert.strictEqual(batchData.success, true);
    assert.strictEqual(batchData.data.ingested, 2);
    assert.strictEqual(batchData.data.optedOut, false);

    // B. Privacy Opt-Out via Header (DNT: 1)
    const optOutRes = await fetch(`${BASE_URL}/api/v1/analytics/events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'DNT': '1'
      },
      body: JSON.stringify({
        events: [
          {
            sessionId: 'sess-optout-001',
            mediaId: 'media-003',
            platform: 'linux',
            eventType: 'start',
            startupTimeMs: 310
          }
        ]
      })
    });
    assert.strictEqual(optOutRes.status, 200);
    const optOutData = await optOutRes.json();
    assert.strictEqual(optOutData.data.ingested, 0);
    assert.strictEqual(optOutData.data.optedOut, true);
  });

  test('11. Ethical Sponsor Campaigns and Impression / Click Tracking', async () => {
    // Fetch active sponsors
    const sponsorRes = await fetch(`${BASE_URL}/api/v1/sponsors/active`);
    assert.strictEqual(sponsorRes.status, 200);
    const sponsorData = await sponsorRes.json();
    assert.strictEqual(sponsorData.success, true);
    assert.ok(sponsorData.data.length >= 2);

    const blenderSponsor = sponsorData.data.find((s: any) => s.id === 'sp-blender-01');
    assert.ok(blenderSponsor);
    assert.strictEqual(blenderSponsor.sponsorName, 'Blender Foundation');
    assert.strictEqual(blenderSponsor.badgeText, 'Creator Support');

    // Record impression
    const impRes = await fetch(`${BASE_URL}/api/v1/sponsors/impression`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaignId: 'sp-blender-01' })
    });
    assert.strictEqual(impRes.status, 200);

    // Record click
    const clickRes = await fetch(`${BASE_URL}/api/v1/sponsors/click`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaignId: 'sp-blender-01' })
    });
    assert.strictEqual(clickRes.status, 200);

    // Verify 404 for non-existent campaign ID (DEF-P6-01 remediation)
    const invalidImpRes = await fetch(`${BASE_URL}/api/v1/sponsors/impression`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaignId: 'sp-non-existent' })
    });
    assert.strictEqual(invalidImpRes.status, 404);
  });
});

