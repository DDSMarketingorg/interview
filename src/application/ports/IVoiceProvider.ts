export interface IVoiceProvider {
  initiateCall(to: string, callbackHost: string): Promise<{ callSid: string }>;
}
