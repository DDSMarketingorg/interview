export interface ISpeechToText {
  transcribe(audioBuffer: Buffer, mimeType?: string): Promise<string>;
}
