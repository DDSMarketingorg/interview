import { IGHLGateway, GHLContact } from '../../application/ports/IGHLGateway';

const GHL_BASE_URL = 'https://services.leadconnectorhq.com';

export class GHLGateway implements IGHLGateway {
  constructor(
    private readonly apiKey: string,
    private readonly locationId: string,
    private readonly calendarId: string,
  ) {}

  private get headers(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
      Version: '2021-07-28',
    };
  }

  async getContact(contactId: string): Promise<GHLContact> {
    const res = await fetch(`${GHL_BASE_URL}/contacts/${contactId}`, {
      headers: this.headers,
    });
    if (!res.ok) throw new Error(`GHL getContact failed: ${res.status}`);

    const data = await res.json() as {
      contact: {
        id: string;
        firstName: string;
        phone: string;
        email: string | null;
        dndSettings?: { Call?: { status: string } };
      };
    };

    const c = data.contact;
    return {
      id: c.id,
      firstName: c.firstName,
      phone: c.phone,
      email: c.email ?? null,
      dndCall: c.dndSettings?.Call?.status === 'active',
    };
  }

  async createNote(contactId: string, body: string): Promise<void> {
    const res = await fetch(`${GHL_BASE_URL}/contacts/${contactId}/notes`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ body }),
    });
    if (!res.ok) throw new Error(`GHL createNote failed: ${res.status}`);
  }

  async updateContactStage(contactId: string, stage: string): Promise<void> {
    const res = await fetch(`${GHL_BASE_URL}/contacts/${contactId}`, {
      method: 'PUT',
      headers: this.headers,
      body: JSON.stringify({ customField: { ai_call_stage: stage } }),
    });
    if (!res.ok) throw new Error(`GHL updateContactStage failed: ${res.status}`);
  }

  async createAppointment(contactId: string, isoDateTime: string): Promise<void> {
    const res = await fetch(`${GHL_BASE_URL}/calendars/events/appointments`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({
        calendarId: this.calendarId,
        locationId: this.locationId,
        contactId,
        startTime: isoDateTime,
        title: 'AI-Scheduled Dental Appointment',
      }),
    });
    if (!res.ok) throw new Error(`GHL createAppointment failed: ${res.status}`);
  }

  async setDnd(contactId: string, enabled: boolean): Promise<void> {
    const res = await fetch(`${GHL_BASE_URL}/contacts/${contactId}`, {
      method: 'PUT',
      headers: this.headers,
      body: JSON.stringify({
        dndSettings: {
          Call: { status: enabled ? 'active' : 'inactive', message: 'Opted out via AI call' },
        },
      }),
    });
    if (!res.ok) throw new Error(`GHL setDnd failed: ${res.status}`);
  }
}
