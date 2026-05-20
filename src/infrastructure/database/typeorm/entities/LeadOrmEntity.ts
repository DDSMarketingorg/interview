import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, OneToOne, OneToMany,
} from 'typeorm';
import { LeadDncOrmEntity } from './LeadDncOrmEntity';
import { CallLogOrmEntity } from './CallLogOrmEntity';

@Entity('leads')
export class LeadOrmEntity {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ name: 'ghl_contact_id', unique: true })
  ghlContactId!: string;

  @Column({ name: 'first_name' })
  firstName!: string;

  @Column()
  phone!: string;

  @Column({ nullable: true, type: 'varchar' })
  email!: string | null;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt!: Date;

  @OneToOne(() => LeadDncOrmEntity, (dnc) => dnc.lead, { cascade: true })
  dnc!: LeadDncOrmEntity;

  @OneToMany(() => CallLogOrmEntity, (call) => call.lead)
  calls!: CallLogOrmEntity[];
}
