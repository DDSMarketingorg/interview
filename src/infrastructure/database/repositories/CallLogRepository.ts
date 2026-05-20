import { DataSource } from 'typeorm';
import { ICallLogRepository } from '../../../domain/repositories/ICallLogRepository';
import { Call, CallEscalation, CallStatus } from '../../../domain/entities/Call';
import { Transcript } from '../../../domain/entities/Transcript';
import { CallLogOrmEntity } from '../typeorm/entities/CallLogOrmEntity';
import { TranscriptOrmEntity } from '../typeorm/entities/TranscriptOrmEntity';
import { CallEscalationOrmEntity } from '../typeorm/entities/CallEscalationOrmEntity';

export class CallLogRepository implements ICallLogRepository {
  constructor(private readonly dataSource: DataSource) {}

  private get callLogs() {
    return this.dataSource.getRepository(CallLogOrmEntity);
  }
  private get transcripts() {
    return this.dataSource.getRepository(TranscriptOrmEntity);
  }
  private get escalations() {
    return this.dataSource.getRepository(CallEscalationOrmEntity);
  }

  async create(leadId: string, twilioCallSid: string): Promise<Call> {
    const row = this.callLogs.create({
      leadId,
      twilioCallSid,
      status: 'pending',
      startedAt: new Date(),
      endedAt: null,
    });
    const saved = await this.callLogs.save(row);
    return this.toCallEntity(saved);
  }

  async findByCallSid(callSid: string): Promise<Call | null> {
    const row = await this.callLogs.findOneBy({ twilioCallSid: callSid });
    return row ? this.toCallEntity(row) : null;
  }

  async updateStatus(callLogId: string, status: CallStatus, endedAt?: Date): Promise<void> {
    await this.callLogs.update(callLogId, { status, endedAt: endedAt ?? null });
  }

  async appendTurn(
    callLogId: string,
    role: Transcript['role'],
    content: string,
    turnIndex: number,
  ): Promise<Transcript> {
    const row = this.transcripts.create({ callLogId, role, content, turnIndex });
    const saved = await this.transcripts.save(row);
    return this.toTranscriptEntity(saved);
  }

  async getTranscripts(callLogId: string): Promise<Transcript[]> {
    const rows = await this.transcripts.find({
      where: { callLogId },
      order: { turnIndex: 'ASC' },
    });
    return rows.map(this.toTranscriptEntity);
  }

  async recordEscalation(callLogId: string, reason: string): Promise<CallEscalation> {
    const row = this.escalations.create({ callLogId, reason });
    const saved = await this.escalations.save(row);
    return { id: saved.id, callLogId: saved.callLogId, reason: saved.reason, escalatedAt: saved.escalatedAt };
  }

  private toCallEntity(row: CallLogOrmEntity): Call {
    return {
      id: row.id,
      leadId: row.leadId,
      twilioCallSid: row.twilioCallSid,
      status: row.status,
      startedAt: row.startedAt,
      endedAt: row.endedAt,
    };
  }

  private toTranscriptEntity(row: TranscriptOrmEntity): Transcript {
    return {
      id: row.id,
      callLogId: row.callLogId,
      role: row.role,
      content: row.content,
      turnIndex: row.turnIndex,
      timestamp: row.timestamp,
    };
  }
}
