import { Request, Response, NextFunction } from 'express';
import { IGHLGateway } from '../../../application/ports/IGHLGateway';

/**
 * TCPA compliance middleware:
 * 1. Checks GHL contact DND flag (source of truth)
 * 2. Enforces TCPA call time window (8am–9pm in UTC for demo; extend to tz-aware in prod)
 */
export function makeDncCheck(ghlGateway: IGHLGateway) {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    const { contact } = req.body as { contact?: { id?: string } };

    if (!contact?.id) {
      res.status(400).json({ error: 'Missing contact.id in payload' });
      return;
    }

    try {
      const ghlContact = await ghlGateway.getContact(contact.id);

      if (ghlContact.dndCall) {
        res.status(200).json({ skipped: true, reason: 'DNC flag set on GHL contact' });
        return;
      }

      // TCPA: Do Not Call before 8am or after 9pm (caller's local time).
      // In production, derive timezone from the lead's phone area code or GHL custom field.
      const hour = new Date().getUTCHours();
      if (hour < 8 || hour >= 21) {
        res.status(200).json({ skipped: true, reason: 'Outside TCPA-permitted call window (8am–9pm)' });
        return;
      }

      next();
    } catch (err) {
      next(err);
    }
  };
}
