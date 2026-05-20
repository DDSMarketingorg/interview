import { CollectedField, FieldName } from '../entities/CollectedFields';

export interface ICollectedFieldsRepository {
  upsert(callLogId: string, fieldName: FieldName, fieldValue: string): Promise<CollectedField>;
  findByCallLogId(callLogId: string): Promise<CollectedField[]>;
}
