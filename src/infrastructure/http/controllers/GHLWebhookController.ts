import { Request, Response, NextFunction } from 'express';
import { HandleInboundLeadUseCase, DncBlockedError } from '../../../application/usecases/HandleInboundLeadUseCase';

interface GHLWebhookPayload {
  event: string;
  contact: {
    id: string;
    firstName: string;
    phone: string;
    email?: string;
  };
}

export class GHLWebhookController {
  constructor(private readonly handleInboundLead: HandleInboundLeadUseCase) {}

  async handle(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const payload = req.body as GHLWebhookPayload;

      if (payload.event !== 'contact.created') {
        res.status(200).json({ skipped: true, reason: `Unhandled event: ${payload.event}` });
        return;
      }

      const { contact } = payload;
      const { callSid } = await this.handleInboundLead.execute({
        ghlContactId: contact.id,
        firstName: contact.firstName,
        phone: contact.phone,
        email: contact.email ?? null,
      });

      res.status(202).json({ status: 'call_initiated', callSid });
    } catch (err) {
      if (err instanceof DncBlockedError) {
        // Log but return 200 — GHL should not retry DNC rejections
        console.warn(`[DNC] ${err.message}`);
        res.status(200).json({ skipped: true, reason: 'DNC' });
        return;
      }
      next(err);
    }
  }
}
