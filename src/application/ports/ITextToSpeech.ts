export interface ITextToSpeech {
  /**
   * Returns an async iterable of μ-law 8kHz audio chunks ready for Twilio Media Streams.
   */
  stream(text: string): AsyncIterable<Buffer>;
}
