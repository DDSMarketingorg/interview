export type TranscriptRole = 'user' | 'assistant';

export interface Transcript {
  id: string;
  callLogId: string;
  role: TranscriptRole;
  content: string;
  turnIndex: number;
  timestamp: Date;
}
