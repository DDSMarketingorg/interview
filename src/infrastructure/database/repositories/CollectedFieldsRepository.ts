import { DataSource } from 'typeorm';
import { ICollectedFieldsRepository } from '../../../domain/repositories/ICollectedFieldsRepository';
import { CollectedField, FieldName } from '../../../domain/entities/CollectedFields';
import { CollectedFieldOrmEntity } from '../typeorm/entities/CollectedFieldOrmEntity';

export class CollectedFieldsRepository implements ICollectedFieldsRepository {
  constructor(private readonly dataSource: DataSource) {}

  private get repo() {
    return this.dataSource.getRepository(CollectedFieldOrmEntity);
  }

  async upsert(callLogId: string, fieldName: FieldName, fieldValue: string): Promise<CollectedField> {
    await this.repo.upsert(
      { callLogId, fieldName, fieldValue },
      ['callLogId', 'fieldName'],
    );
    const row = await this.repo.findOneOrFail({ where: { callLogId, fieldName } });
    return this.toEntity(row);
  }

  async findByCallLogId(callLogId: string): Promise<CollectedField[]> {
    const rows = await this.repo.findBy({ callLogId });
    return rows.map(this.toEntity);
  }

  private toEntity(row: CollectedFieldOrmEntity): CollectedField {
    return {
      id: row.id,
      callLogId: row.callLogId,
      fieldName: row.fieldName,
      fieldValue: row.fieldValue,
      collectedAt: row.collectedAt,
    };
  }
}
