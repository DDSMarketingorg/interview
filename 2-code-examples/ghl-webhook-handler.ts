import { Request, Response } from "express";
import { Contact, DndSettingsSchema } from "@gohighlevel/api-client/dist/lib/code/contacts/models/contacts";
declare const ComplianceManager: {
    checkCompliance: (phone: string | undefined, dnd: boolean | undefined, dndSettings: DndSettingsSchema | undefined) => Promise<{ canCall: boolean, reason: string }>;
};
declare const VoicePipeline: {
    startPipeline: (contact: Contact) => Promise<void>;
};
declare const EventLogger: {
    logEvent: (event: { contactId: string, event: string, reason?: string, error?: string }) => Promise<void>;
};

export const ghlWebhookHandler = async (req: Request, res: Response) => {
    const { event, contact } = req.body;
    const { dnd, dndSettings, phone } = contact as Contact;
    // dndSettings contains settings for phone, email, etc.
    try {
        if (event === 'contact.created') {
            const complianceCheck = await ComplianceManager.checkCompliance(phone, dnd, dndSettings);
            if (complianceCheck.canCall) {
                await VoicePipeline.startPipeline(contact);
            } else {
                EventLogger.logEvent({
                    contactId: contact.id,
                    event: 'call_blocked',
                    reason: complianceCheck.reason
                });
            }
        }
        res.status(200).json({ success: true });
    } catch (error) {
        EventLogger.logEvent({
            contactId: contact.id,
            event: 'webhook_error',
            error: error.message
        });
        res.status(500).json({ error: 'Internal server error' });
    }
}