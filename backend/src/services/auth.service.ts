import { Database } from '../db/database.ts';
import type { User, PlaybackBookmark } from '../types/index.ts';
import { CryptoUtil } from '../utils/crypto.ts';

export class AuthService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  register(email: string, password: string, displayName: string): { user: Omit<User, 'passwordHash'>; token: string } {
    const existing = this.db.getUserByEmail(email.toLowerCase().trim());
    if (existing) {
      throw new Error('Email is already registered');
    }

    if (!password || password.length < 6) {
      throw new Error('Password must be at least 6 characters');
    }

    const user: User = {
      id: CryptoUtil.randomId('user'),
      email: email.toLowerCase().trim(),
      passwordHash: CryptoUtil.hashPassword(password),
      displayName: displayName.trim() || 'Viewer',
      role: 'user',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    this.db.createUser(user);

    const token = CryptoUtil.generateToken({
      userId: user.id,
      email: user.email,
      role: user.role
    }, 60 * 24); // 24 hours

    const { passwordHash, ...safeUser } = user;
    return { user: safeUser, token };
  }

  login(email: string, password: string): { user: Omit<User, 'passwordHash'>; token: string } {
    const user = this.db.getUserByEmail(email.toLowerCase().trim());
    if (!user) {
      throw new Error('Invalid email or password');
    }

    const valid = CryptoUtil.verifyPassword(password, user.passwordHash);
    if (!valid) {
      throw new Error('Invalid email or password');
    }

    const token = CryptoUtil.generateToken({
      userId: user.id,
      email: user.email,
      role: user.role
    }, 60 * 24);

    const { passwordHash, ...safeUser } = user;
    return { user: safeUser, token };
  }

  getUserFromToken(token: string): Omit<User, 'passwordHash'> | null {
    const payload = CryptoUtil.verifyToken<{ userId: string }>(token);
    if (!payload?.userId) return null;
    const user = this.db.getUserById(payload.userId);
    if (!user) return null;
    const { passwordHash, ...safeUser } = user;
    return safeUser;
  }

  syncGuestData(
    userId: string,
    guestBookmarks: { mediaId: string; positionSeconds: number; durationSeconds: number }[],
    guestWatchlist: string[]
  ): { syncedBookmarks: number; syncedWatchlist: number } {
    let syncedBookmarks = 0;
    for (const b of guestBookmarks) {
      this.db.saveBookmark({
        userId,
        mediaId: b.mediaId,
        positionSeconds: b.positionSeconds,
        durationSeconds: b.durationSeconds,
        completedPercentage: Math.min(100, Math.round((b.positionSeconds / b.durationSeconds) * 100)),
        updatedAt: new Date().toISOString()
      });
      syncedBookmarks++;
    }

    let syncedWatchlist = 0;
    for (const mediaId of guestWatchlist) {
      this.db.addToWatchlist(userId, mediaId);
      syncedWatchlist++;
    }

    return { syncedBookmarks, syncedWatchlist };
  }
}
