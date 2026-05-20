export type CallStatus = 'pending' | 'active' | 'completed' | 'failed';

export interface Call {
  id: string;
  leadId: string;
  twilioCallSid: string;
  status: CallStatus;
  startedAt: Date;
  endedAt: Date | null;
}

export interface CallEscalation {
  id: string;
  callLogId: string;
  reason: string;
  escalatedAt: Date;
}
