import { ICallLogRepository } from '../../domain/repositories/ICallLogRepository';
import { ICollectedFieldsRepository } from '../../domain/repositories/ICollectedFieldsRepository';
import { ILeadRepository } from '../../domain/repositories/ILeadRepository';
import { IGHLGateway } from '../ports/IGHLGateway';
import { QualificationResult } from '../../domain/entities/CollectedFields';

export class FinalizeCallUseCase {
  constructor(
    private readonly callLogRepo: ICallLogRepository,
    private readonly collectedFieldsRepo: ICollectedFieldsRepository,
    private readonly leadRepo: ILeadRepository,
    private readonly ghlGateway: IGHLGateway,
  ) {}

  async execute(callSid: string, outcome: QualificationResult['outcome']): Promise<void> {
    const call = await this.callLogRepo.findByCallSid(callSid);
    if (!call) return;

    const isEscalated = outcome === 'escalated';
    const finalStatus = isEscalated || outcome === 'qualified' ? 'completed' : 'failed';
    await this.callLogRepo.updateStatus(call.id, finalStatus, new Date());

    const lead = await this.leadRepo.findById(call.leadId);
    if (!lead) return;

    const fields = await this.collectedFieldsRepo.findByCallLogId(call.id);
    const byName = Object.fromEntries(fields.map((f) => [f.fieldName, f.fieldValue]));

    const noteParts = [
      `AI Voice Intake — ${new Date().toISOString()}`,
      `Outcome: ${outcome}`,
      byName['pain_level'] ? `Pain level: ${byName['pain_level']}` : null,
      byName['insurance_provider'] ? `Insurance: ${byName['insurance_provider']}` : null,
      byName['preferred_slot'] ? `Preferred slot: ${byName['preferred_slot']}` : null,
      isEscalated ? '⚠️ Escalated to human — review required' : null,
    ]
      .filter(Boolean)
      .join('\n');

    await this.ghlGateway.createNote(lead.ghlContactId, noteParts);

    const stage = isEscalated ? 'Escalated' : outcome === 'qualified' ? 'Qualified' : 'No Answer';
    await this.ghlGateway.updateContactStage(lead.ghlContactId, stage);

    if (byName['preferred_slot'] && !isEscalated) {
      // Convert "2025-09-07 15:30" to ISO 8601
      const isoSlot = new Date(byName['preferred_slot']).toISOString();
      await this.ghlGateway.createAppointment(lead.ghlContactId, isoSlot);
    }
  }
}
