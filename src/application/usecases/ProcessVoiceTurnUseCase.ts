import { ICallLogRepository } from '../../domain/repositories/ICallLogRepository';
import { ICollectedFieldsRepository } from '../../domain/repositories/ICollectedFieldsRepository';
import { ISpeechToText } from '../ports/ISpeechToText';
import { ITextToSpeech } from '../ports/ITextToSpeech';
import { ILanguageModel, ChatMessage, ToolEvent } from '../ports/ILanguageModel';

export interface VoiceTurnInput {
  callSid: string;
  audioBuffer: Buffer;
  conversationHistory: ChatMessage[];
  turnIndex: number;
}

export interface VoiceTurnOutput {
  transcript: string;
  reply: string;
  audioStream: AsyncIterable<Buffer>;
  toolEvents: ToolEvent[];
  shouldEnd: boolean;
}

export class ProcessVoiceTurnUseCase {
  constructor(
    private readonly callLogRepo: ICallLogRepository,
    private readonly collectedFieldsRepo: ICollectedFieldsRepository,
    private readonly stt: ISpeechToText,
    private readonly tts: ITextToSpeech,
    private readonly llm: ILanguageModel,
  ) {}

  async execute(input: VoiceTurnInput): Promise<VoiceTurnOutput> {
    const call = await this.callLogRepo.findByCallSid(input.callSid);
    if (!call) throw new Error(`Call not found for SID: ${input.callSid}`);

    const transcript = await this.stt.transcribe(input.audioBuffer);
    await this.callLogRepo.appendTurn(call.id, 'user', transcript, input.turnIndex);

    const { reply, toolEvents } = await this.llm.chat(input.conversationHistory, transcript);
    await this.callLogRepo.appendTurn(call.id, 'assistant', reply, input.turnIndex + 1);

    // Persist any structured fields extracted by tool calls
    for (const event of toolEvents) {
      if (event.type === 'collect_pain_info') {
        await this.collectedFieldsRepo.upsert(call.id, 'pain_level', event.pain_level);
      } else if (event.type === 'collect_insurance') {
        await this.collectedFieldsRepo.upsert(call.id, 'insurance_provider', event.provider);
      } else if (event.type === 'collect_appointment_preference') {
        const slot = `${event.preferred_date} ${event.preferred_time}`;
        await this.collectedFieldsRepo.upsert(call.id, 'preferred_slot', slot);
      } else if (event.type === 'escalate_to_human') {
        await this.callLogRepo.recordEscalation(call.id, event.reason);
      }
    }

    const shouldEnd = toolEvents.some(
      (e) => e.type === 'end_conversation' || e.type === 'escalate_to_human',
    );

    const audioStream = this.tts.stream(reply);

    return { transcript, reply, audioStream, toolEvents, shouldEnd };
  }
}
