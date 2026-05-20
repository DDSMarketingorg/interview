import {
  Entity, PrimaryGeneratedColumn, Column, OneToOne, JoinColumn, CreateDateColumn,
} from 'typeorm';
import { CallLogOrmEntity } from './CallLogOrmEntity';

@Entity('call_escalations')
export class CallEscalationOrmEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'call_log_id' })
  callLogId!: string;

  @Column({ type: 'varchar' })
  reason!: string;

  @CreateDateColumn({ name: 'escalated_at', type: 'timestamptz' })
  escalatedAt!: Date;

  @OneToOne(() => CallLogOrmEntity, (c) => c.escalation)
  @JoinColumn({ name: 'call_log_id' })
  callLog!: CallLogOrmEntity;
}
