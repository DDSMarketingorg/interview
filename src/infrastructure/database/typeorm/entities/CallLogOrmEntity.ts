import {
  Entity, PrimaryGeneratedColumn, Column, ManyToOne, OneToMany, OneToOne, JoinColumn,
} from 'typeorm';
import { LeadOrmEntity } from './LeadOrmEntity';
import { TranscriptOrmEntity } from './TranscriptOrmEntity';
import { CollectedFieldOrmEntity } from './CollectedFieldOrmEntity';
import { CallEscalationOrmEntity } from './CallEscalationOrmEntity';

export type CallStatusEnum = 'pending' | 'active' | 'completed' | 'failed';

@Entity('call_logs')
export class CallLogOrmEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'lead_id' })
  leadId!: string;

  @Column({ name: 'twilio_call_sid', unique: true })
  twilioCallSid!: string;

  @Column({
    type: 'enum',
    enum: ['pending', 'active', 'completed', 'failed'],
    default: 'pending',
  })
  status!: CallStatusEnum;

  @Column({ name: 'started_at', type: 'timestamptz' })
  startedAt!: Date;

  @Column({ name: 'ended_at', type: 'timestamptz', nullable: true })
  endedAt!: Date | null;

  @ManyToOne(() => LeadOrmEntity, (lead) => lead.calls)
  @JoinColumn({ name: 'lead_id' })
  lead!: LeadOrmEntity;

  @OneToMany(() => TranscriptOrmEntity, (t) => t.callLog, { cascade: true })
  transcripts!: TranscriptOrmEntity[];

  @OneToMany(() => CollectedFieldOrmEntity, (f) => f.callLog, { cascade: true })
  collectedFields!: CollectedFieldOrmEntity[];

  @OneToOne(() => CallEscalationOrmEntity, (e) => e.callLog, { cascade: true })
  escalation!: CallEscalationOrmEntity | null;
}
