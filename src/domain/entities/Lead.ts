export interface Lead {
  id: string;
  ghlContactId: string;
  firstName: string;
  phone: string;
  email: string | null;
  createdAt: Date;
}

export interface LeadDnc {
  id: string;
  leadId: string;
  isDnc: boolean;
  dncSetAt: Date | null;
  dncReason: 'opted_out' | 'ghl_flag' | 'manual' | null;
}
