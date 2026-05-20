import {
  Entity, PrimaryGeneratedColumn, Column, OneToOne, JoinColumn,
} from 'typeorm';
import { LeadOrmEntity } from './LeadOrmEntity';

@Entity('lead_dnc')
export class LeadDncOrmEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'lead_id' })
  leadId!: string;

  @Column({ name: 'is_dnc', default: false })
  isDnc!: boolean;

  @Column({ name: 'dnc_set_at', type: 'timestamptz', nullable: true })
  dncSetAt!: Date | null;

  @Column({ name: 'dnc_reason', type: 'varchar', nullable: true })
  dncReason!: 'opted_out' | 'ghl_flag' | 'manual' | null;

  @OneToOne(() => LeadOrmEntity, (lead) => lead.dnc)
  @JoinColumn({ name: 'lead_id' })
  lead!: LeadOrmEntity;
}
