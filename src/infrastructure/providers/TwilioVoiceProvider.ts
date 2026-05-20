import twilio from 'twilio';
import { IVoiceProvider } from '../../application/ports/IVoiceProvider';

export class TwilioVoiceProvider implements IVoiceProvider {
  private readonly client: twilio.Twilio;

  constructor(
    private readonly accountSid: string,
    private readonly authToken: string,
    private readonly fromNumber: string,
  ) {
    this.client = twilio(accountSid, authToken);
  }

  async initiateCall(to: string, callbackHost: string): Promise<{ callSid: string }> {
    const { VoiceResponse } = twilio.twiml;
    const response = new VoiceResponse();
    const connect = response.connect();
    // <Connect><Stream> creates bidirectional audio — TwiML after this is unreachable
    // until the WebSocket server sends the 'stop' message.
    connect.stream({ url: `wss://${callbackHost}/voice/stream` });

    const call = await this.client.calls.create({
      to,
      from: this.fromNumber,
      twiml: response.toString(),
    });

    return { callSid: call.sid };
  }
}
