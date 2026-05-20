import 'reflect-metadata';
import { DataSource } from 'typeorm';
import { LeadOrmEntity } from './entities/LeadOrmEntity';
import { LeadDncOrmEntity } from './entities/LeadDncOrmEntity';
import { CallLogOrmEntity } from './entities/CallLogOrmEntity';
import { CallEscalationOrmEntity } from './entities/CallEscalationOrmEntity';
import { TranscriptOrmEntity } from './entities/TranscriptOrmEntity';
import { CollectedFieldOrmEntity } from './entities/CollectedFieldOrmEntity';

const isProduction = process.env.NODE_ENV === 'production';

export const AppDataSource = new DataSource({
  type: 'postgres',
  url: process.env.DATABASE_URL,
  ssl: isProduction ? { rejectUnauthorized: true } : false,
  entities: [
    LeadOrmEntity,
    LeadDncOrmEntity,
    CallLogOrmEntity,
    CallEscalationOrmEntity,
    TranscriptOrmEntity,
    CollectedFieldOrmEntity,
  ],
  migrations: ['src/infrastructure/database/typeorm/migrations/*.ts'],
  migrationsTableName: 'typeorm_migrations',
  synchronize: false,
  logging: !isProduction,
});
