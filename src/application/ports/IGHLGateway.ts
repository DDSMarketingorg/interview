export interface GHLContact {
  id: string;
  firstName: string;
  phone: string;
  email: string | null;
  dndCall: boolean;
}

export interface IGHLGateway {
  getContact(contactId: string): Promise<GHLContact>;
  createNote(contactId: string, body: string): Promise<void>;
  updateContactStage(contactId: string, stage: string): Promise<void>;
  createAppointment(contactId: string, isoDateTime: string): Promise<void>;
  setDnd(contactId: string, enabled: boolean): Promise<void>;
}
