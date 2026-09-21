import crypto from 'node:crypto';

const JWT_SECRET = process.env.JWT_SECRET || 'cross-platform-streaming-jwt-secret-key-2026';

export class CryptoUtil {
  static hashPassword(password: string): string {
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.scryptSync(password, salt, 64).toString('hex');
    return `${salt}:${hash}`;
  }

  static verifyPassword(password: string, storedHash: string): boolean {
    const [salt, originalHash] = storedHash.split(':');
    if (!salt || !originalHash) return false;
    const computedHash = crypto.scryptSync(password, salt, 64).toString('hex');
    return crypto.timingSafeEqual(Buffer.from(computedHash, 'hex'), Buffer.from(originalHash, 'hex'));
  }

  static generateToken(payload: object, expiresInMinutes = 60): string {
    const header = { alg: 'HS256', typ: 'JWT' };
    const exp = Math.floor(Date.now() / 1000) + expiresInMinutes * 60;
    const body = { ...payload, exp };

    const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64url');
    const encodedBody = Buffer.from(JSON.stringify(body)).toString('base64url');

    const signature = crypto
      .createHmac('sha256', JWT_SECRET)
      .update(`${encodedHeader}.${encodedBody}`)
      .digest('base64url');

    return `${encodedHeader}.${encodedBody}.${signature}`;
  }

  static verifyToken<T>(token: string): T | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      const [headerB64, bodyB64, signature] = parts;

      const expectedSignature = crypto
        .createHmac('sha256', JWT_SECRET)
        .update(`${headerB64}.${bodyB64}`)
        .digest('base64url');

      if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) {
        return null;
      }

      const body = JSON.parse(Buffer.from(bodyB64, 'base64url').toString('utf8'));
      if (body.exp && body.exp < Math.floor(Date.now() / 1000)) {
        return null; // Expired
      }
      return body as T;
    } catch {
      return null;
    }
  }

  static randomId(prefix = 'id'): string {
    return `${prefix}-${crypto.randomBytes(8).toString('hex')}`;
  }
}
