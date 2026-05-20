import {
  Entity, PrimaryGeneratedColumn, Column, ManyToOne, JoinColumn, CreateDateColumn,
} from 'typeorm';
import { CallLogOrmEntity } from './CallLogOrmEntity';

@Entity('transcripts')
export class TranscriptOrmEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'call_log_id' })
  callLogId!: string;

  @Column({ type: 'enum', enum: ['user', 'assistant'] })
  role!: 'user' | 'assistant';

  @Column({ type: 'text' })
  content!: string;

  @Column({ name: 'turn_index', type: 'int' })
  turnIndex!: number;

  @CreateDateColumn({ name: 'timestamp', type: 'timestamptz' })
  timestamp!: Date;

  @ManyToOne(() => CallLogOrmEntity, (c) => c.transcripts)
  @JoinColumn({ name: 'call_log_id' })
  callLog!: CallLogOrmEntity;
}
