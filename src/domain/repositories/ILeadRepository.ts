import { Lead, LeadDnc } from '../entities/Lead';

export interface ILeadRepository {
  upsert(lead: Omit<Lead, 'id' | 'createdAt'>): Promise<Lead>;
  findByGhlContactId(ghlContactId: string): Promise<Lead | null>;
  findById(id: string): Promise<Lead | null>;
  getDncStatus(leadId: string): Promise<LeadDnc | null>;
  setDnc(leadId: string, reason: LeadDnc['dncReason']): Promise<void>;
}
