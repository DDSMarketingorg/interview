export type FieldName = 'pain_level' | 'insurance_provider' | 'preferred_slot';

export interface CollectedField {
  id: string;
  callLogId: string;
  fieldName: FieldName;
  fieldValue: string;
  collectedAt: Date;
}

export interface QualificationResult {
  painLevel: string | null;
  insuranceProvider: string | null;
  preferredSlot: string | null;
  escalated: boolean;
  escalationReason: string | null;
  outcome: 'qualified' | 'escalated' | 'declined' | 'voicemail' | 'no_answer';
}
