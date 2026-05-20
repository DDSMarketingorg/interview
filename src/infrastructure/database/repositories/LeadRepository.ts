import { DataSource } from 'typeorm';
import { ILeadRepository } from '../../../domain/repositories/ILeadRepository';
import { Lead, LeadDnc } from '../../../domain/entities/Lead';
import { LeadOrmEntity } from '../typeorm/entities/LeadOrmEntity';
import { LeadDncOrmEntity } from '../typeorm/entities/LeadDncOrmEntity';

export class LeadRepository implements ILeadRepository {
  constructor(private readonly dataSource: DataSource) {}

  private get leads() {
    return this.dataSource.getRepository(LeadOrmEntity);
  }

  private get leadDnc() {
    return this.dataSource.getRepository(LeadDncOrmEntity);
  }

  async upsert(input: Omit<Lead, 'id' | 'createdAt'>): Promise<Lead> {
    const existing = await this.leads.findOneBy({ ghlContactId: input.ghlContactId });
    if (existing) return this.toEntity(existing);

    const lead = this.leads.create({
      ghlContactId: input.ghlContactId,
      firstName: input.firstName,
      phone: input.phone,
      email: input.email,
    });
    const saved = await this.leads.save(lead);

    // Create default DNC record
    const dnc = this.leadDnc.create({ leadId: saved.id, isDnc: false });
    await this.leadDnc.save(dnc);

    return this.toEntity(saved);
  }

  async findByGhlContactId(ghlContactId: string): Promise<Lead | null> {
    const row = await this.leads.findOneBy({ ghlContactId });
    return row ? this.toEntity(row) : null;
  }

  async findById(id: string): Promise<Lead | null> {
    const row = await this.leads.findOneBy({ id });
    return row ? this.toEntity(row) : null;
  }

  async getDncStatus(leadId: string): Promise<LeadDnc | null> {
    const row = await this.leadDnc.findOneBy({ leadId });
    if (!row) return null;
    return {
      id: row.id,
      leadId: row.leadId,
      isDnc: row.isDnc,
      dncSetAt: row.dncSetAt,
      dncReason: row.dncReason,
    };
  }

  async setDnc(leadId: string, reason: LeadDnc['dncReason']): Promise<void> {
    await this.leadDnc.upsert(
      { leadId, isDnc: true, dncSetAt: new Date(), dncReason: reason },
      ['leadId'],
    );
  }

  private toEntity(row: LeadOrmEntity): Lead {
    return {
      id: row.id,
      ghlContactId: row.ghlContactId,
      firstName: row.firstName,
      phone: row.phone,
      email: row.email,
      createdAt: row.createdAt,
    };
  }
}
