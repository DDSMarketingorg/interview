import {
  Entity, PrimaryGeneratedColumn, Column, ManyToOne, JoinColumn, CreateDateColumn, Unique,
} from 'typeorm';
import { CallLogOrmEntity } from './CallLogOrmEntity';
import { FieldName } from '../../../../domain/entities/CollectedFields';

@Entity('collected_fields')
@Unique(['callLogId', 'fieldName'])
export class CollectedFieldOrmEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'call_log_id' })
  callLogId!: string;

  @Column({
    name: 'field_name',
    type: 'enum',
    enum: ['pain_level', 'insurance_provider', 'preferred_slot'],
  })
  fieldName!: FieldName;

  @Column({ name: 'field_value', type: 'varchar' })
  fieldValue!: string;

  @CreateDateColumn({ name: 'collected_at', type: 'timestamptz' })
  collectedAt!: Date;

  @ManyToOne(() => CallLogOrmEntity, (c) => c.collectedFields)
  @JoinColumn({ name: 'call_log_id' })
  callLog!: CallLogOrmEntity;
}
