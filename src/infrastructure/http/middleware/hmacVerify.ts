import { Request, Response, NextFunction } from 'express';
import { createHmac, timingSafeEqual } from 'crypto';

/**
 * Validates the x-ghl-signature HMAC-SHA256 header on GHL webhook payloads.
 * Prevents spoofed lead injection attacks.
 */
export function hmacVerify(secret: string) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const signature = req.headers['x-ghl-signature'] as string | undefined;
    if (!signature) {
      res.status(401).json({ error: 'Missing x-ghl-signature' });
      return;
    }

    const rawBody = JSON.stringify(req.body);
    const expected = createHmac('sha256', secret).update(rawBody).digest('hex');

    let signaturesMatch: boolean;
    try {
      signaturesMatch = timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
    } catch {
      signaturesMatch = false;
    }

    if (!signaturesMatch) {
      res.status(401).json({ error: 'Invalid webhook signature' });
      return;
    }

    next();
  };
}
