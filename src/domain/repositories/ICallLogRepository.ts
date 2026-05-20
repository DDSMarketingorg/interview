import { Call, CallEscalation, CallStatus } from '../entities/Call';
import { Transcript } from '../entities/Transcript';

export interface ICallLogRepository {
  create(leadId: string, twilioCallSid: string): Promise<Call>;
  findByCallSid(callSid: string): Promise<Call | null>;
  updateStatus(callLogId: string, status: CallStatus, endedAt?: Date): Promise<void>;
  appendTurn(callLogId: string, role: Transcript['role'], content: string, turnIndex: number): Promise<Transcript>;
  getTranscripts(callLogId: string): Promise<Transcript[]>;
  recordEscalation(callLogId: string, reason: string): Promise<CallEscalation>;
}
