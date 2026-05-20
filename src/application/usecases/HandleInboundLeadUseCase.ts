import { ILeadRepository } from '../../domain/repositories/ILeadRepository';
import { ICallLogRepository } from '../../domain/repositories/ICallLogRepository';
import { IVoiceProvider } from '../ports/IVoiceProvider';
import { IGHLGateway } from '../ports/IGHLGateway';

interface InboundLeadInput {
  ghlContactId: string;
  firstName: string;
  phone: string;
  email: string | null;
}

export class HandleInboundLeadUseCase {
  constructor(
    private readonly leadRepo: ILeadRepository,
    private readonly callLogRepo: ICallLogRepository,
    private readonly voiceProvider: IVoiceProvider,
    private readonly ghlGateway: IGHLGateway,
    private readonly callbackHost: string,
  ) {}

  async execute(input: InboundLeadInput): Promise<{ callSid: string }> {
    // Fetch GHL contact to check DND flag (source of truth)
    const contact = await this.ghlGateway.getContact(input.ghlContactId);
    if (contact.dndCall) {
      throw new DncBlockedError(`Contact ${input.ghlContactId} has DNC flag set`);
    }

    const lead = await this.leadRepo.upsert({
      ghlContactId: input.ghlContactId,
      firstName: input.firstName,
      phone: input.phone,
      email: input.email,
    });

    const dnc = await this.leadRepo.getDncStatus(lead.id);
    if (dnc?.isDnc) {
      throw new DncBlockedError(`Lead ${lead.id} is on internal DNC list`);
    }

    const { callSid } = await this.voiceProvider.initiateCall(lead.phone, this.callbackHost);
    await this.callLogRepo.create(lead.id, callSid);

    return { callSid };
  }
}

export class DncBlockedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DncBlockedError';
  }
}
