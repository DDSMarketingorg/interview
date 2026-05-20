import { Request, Response, NextFunction } from 'express';
import twilio from 'twilio';

/**
 * Validates the X-Twilio-Signature header on every /voice/* request.
 * Prevents forged Twilio callbacks from reaching the voice pipeline.
 */
export function twilioAuth(req: Request, res: Response, next: NextFunction): void {
  const authToken = process.env.TWILIO_AUTH_TOKEN!;
  const signature = req.headers['x-twilio-signature'] as string | undefined;
  const url = `https://${req.headers.host}${req.originalUrl}`;

  if (!signature) {
    res.status(403).json({ error: 'Missing Twilio signature' });
    return;
  }

  const isValid = twilio.validateRequest(authToken, signature, url, req.body ?? {});
  if (!isValid) {
    res.status(403).json({ error: 'Invalid Twilio signature' });
    return;
  }

  next();
}
