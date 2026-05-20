import { TranscriptRole } from '../../domain/entities/Transcript';
import { QualificationResult } from '../../domain/entities/CollectedFields';

export interface ChatMessage {
  role: TranscriptRole | 'system';
  content: string;
}

export interface LLMTurnResult {
  reply: string;
  toolEvents: ToolEvent[];
}

export type ToolEvent =
  | { type: 'collect_pain_info';         pain_level: string; location?: string; duration?: string }
  | { type: 'collect_insurance';          provider: string; is_self_pay?: boolean }
  | { type: 'collect_appointment_preference'; preferred_date: string; preferred_time: string }
  | { type: 'escalate_to_human';          reason: string }
  | { type: 'end_conversation';           outcome: QualificationResult['outcome'] };

export interface ILanguageModel {
  chat(history: ChatMessage[], userMessage: string): Promise<LLMTurnResult>;
}
