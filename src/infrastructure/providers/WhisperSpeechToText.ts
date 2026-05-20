import { experimental_transcribe as transcribe } from 'ai';
import { openai } from '@ai-sdk/openai';
import { ISpeechToText } from '../../application/ports/ISpeechToText';

export class WhisperSpeechToText implements ISpeechToText {
  async transcribe(audioBuffer: Buffer): Promise<string> {
    const result = await transcribe({
      model: openai.transcription('whisper-1'),
      audio: audioBuffer,
      providerOptions: { openai: { language: 'en' } },
    });
    return result.text.trim();
  }
}

/**
 * Converts Twilio's μ-law 8kHz base64 audio chunks into a WAV buffer
 * suitable for the Whisper API.
 */
export function mulawChunksToWav(chunks: Buffer[]): Buffer {
  const pcmChunks = chunks.map((chunk) => mulawToPcm(chunk));
  const pcmData = Buffer.concat(pcmChunks);
  return buildWavBuffer(pcmData, 8000, 1, 16);
}

function mulawToPcm(mulaw: Buffer): Buffer {
  const pcm = Buffer.alloc(mulaw.length * 2);
  for (let i = 0; i < mulaw.length; i++) {
    const mu = ~mulaw[i] & 0xff;
    const sign = mu & 0x80;
    const exp = (mu >> 4) & 0x07;
    const mantissa = mu & 0x0f;
    let sample = ((mantissa << 1) + 33) << exp;
    if (sign) sample = -sample;
    pcm.writeInt16LE(Math.max(-32768, Math.min(32767, sample)), i * 2);
  }
  return pcm;
}

function buildWavBuffer(pcm: Buffer, sampleRate: number, channels: number, bitDepth: number): Buffer {
  const header = Buffer.alloc(44);
  const byteRate = (sampleRate * channels * bitDepth) / 8;
  const blockAlign = (channels * bitDepth) / 8;

  header.write('RIFF', 0);
  header.writeUInt32LE(36 + pcm.length, 4);
  header.write('WAVE', 8);
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(channels, 22);
  header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(bitDepth, 34);
  header.write('data', 36);
  header.writeUInt32LE(pcm.length, 40);

  return Buffer.concat([header, pcm]);
}
