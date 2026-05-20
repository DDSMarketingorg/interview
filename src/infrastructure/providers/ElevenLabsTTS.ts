import { ElevenLabsClient } from '@elevenlabs/elevenlabs-js';
import { ITextToSpeech } from '../../application/ports/ITextToSpeech';

export class ElevenLabsTTS implements ITextToSpeech {
  private readonly client: ElevenLabsClient;

  constructor(
    apiKey: string,
    private readonly voiceId: string,
  ) {
    this.client = new ElevenLabsClient({ apiKey });
  }

  async *stream(text: string): AsyncIterable<Buffer> {
    // ulaw_8000 is Twilio Media Streams' native format — no re-encoding needed.
    const audioStream = await this.client.textToSpeech.stream(this.voiceId, {
      text,
      modelId: 'eleven_multilingual_v2',
      outputFormat: 'ulaw_8000',
    });

    for await (const chunk of audioStream) {
      yield Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk as Uint8Array);
    }
  }
}
