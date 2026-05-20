import WebSocket from 'ws';
import { ProcessVoiceTurnUseCase } from '../../../application/usecases/ProcessVoiceTurnUseCase';
import { FinalizeCallUseCase } from '../../../application/usecases/FinalizeCallUseCase';
import { ChatMessage } from '../../../application/ports/ILanguageModel';
import { mulawChunksToWav } from '../../providers/WhisperSpeechToText';
import { QualificationResult } from '../../../domain/entities/CollectedFields';

interface TwilioMediaStreamEvent {
  event: 'connected' | 'start' | 'media' | 'stop';
  streamSid?: string;
  start?: { callSid: string; streamSid: string };
  media?: { payload: string; track: string; chunk: string; timestamp: string };
  stop?: { callSid: string };
}

const SILENCE_THRESHOLD_MS = 600;

export class VoiceStreamController {
  constructor(
    private readonly processVoiceTurn: ProcessVoiceTurnUseCase,
    private readonly finalizeCall: FinalizeCallUseCase,
  ) {}

  handle(ws: WebSocket): void {
    let callSid = '';
    let streamSid = '';
    let audioChunks: Buffer[] = [];
    let silenceTimer: ReturnType<typeof setTimeout> | null = null;
    const conversationHistory: ChatMessage[] = [];
    let turnIndex = 0;
    let lastOutcome: QualificationResult['outcome'] = 'no_answer';

    const flushAudio = async () => {
      if (audioChunks.length === 0) return;

      const chunks = [...audioChunks];
      audioChunks = [];

      try {
        const wavBuffer = mulawChunksToWav(chunks);
        const result = await this.processVoiceTurn.execute({
          callSid,
          audioBuffer: wavBuffer,
          conversationHistory: [...conversationHistory],
          turnIndex,
        });

        conversationHistory.push({ role: 'user', content: result.transcript });
        conversationHistory.push({ role: 'assistant', content: result.reply });
        turnIndex += 2;

        // Stream ElevenLabs audio back to Twilio
        for await (const chunk of result.audioStream) {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              event: 'media',
              streamSid,
              media: { payload: chunk.toString('base64') },
            }));
          }
        }

        // Check for end/escalation tool events
        const endEvent = result.toolEvents.find(
          (e) => e.type === 'end_conversation' || e.type === 'escalate_to_human',
        );
        if (endEvent) {
          lastOutcome = endEvent.type === 'escalate_to_human' ? 'escalated'
            : (endEvent as { type: 'end_conversation'; outcome: QualificationResult['outcome'] }).outcome;

          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ event: 'stop', streamSid }));
          }
        }
      } catch (err) {
        console.error('[VoiceStream] Error processing turn:', err);
      }
    };

    ws.on('message', (raw: WebSocket.RawData) => {
      let msg: TwilioMediaStreamEvent;
      try {
        msg = JSON.parse(raw.toString()) as TwilioMediaStreamEvent;
      } catch {
        return;
      }

      switch (msg.event) {
        case 'start':
          callSid = msg.start!.callSid;
          streamSid = msg.start!.streamSid;
          console.info(`[VoiceStream] Call started: ${callSid}`);
          break;

        case 'media':
          if (msg.media?.track === 'inbound') {
            audioChunks.push(Buffer.from(msg.media.payload, 'base64'));

            // Reset silence timer on each incoming chunk
            if (silenceTimer) clearTimeout(silenceTimer);
            silenceTimer = setTimeout(() => void flushAudio(), SILENCE_THRESHOLD_MS);
          }
          break;

        case 'stop':
          if (silenceTimer) clearTimeout(silenceTimer);
          void flushAudio().then(async () => {
            await this.finalizeCall.execute(callSid, lastOutcome).catch((err) =>
              console.error('[VoiceStream] FinalizeCall error:', err),
            );
            console.info(`[VoiceStream] Call ended: ${callSid} — outcome: ${lastOutcome}`);
          });
          break;
      }
    });

    ws.on('error', (err) => {
      console.error('[VoiceStream] WebSocket error:', err);
    });
  }
}
