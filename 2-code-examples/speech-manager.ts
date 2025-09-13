import twilio, { Twilio } from "twilio";

type AudioTask = {
    action: string;
    url?: string;
    duration?: number;
}

export class InMemorySpeechManager {
    private client: Twilio;
    private calls: Map<string, {
        sid: string;
        queue: AudioTask[];
    }> = new Map();
    private twilioNumber: string;
    private streamUrl: string;

    constructor(
        accountSid: string,
        authToken: string,
        twilioNumber: string,
        streamUrl: string
    ) {
        this.twilioNumber = twilioNumber;
        this.streamUrl = streamUrl;
        this.client = twilio(accountSid, authToken);
    }

    /**
     * Called from the twilio webhook to process the queue for a given number when Redirect is part of the TwiML
    */
    processQueue(num: string) {
        const ctx = this.calls.get(num);
        if (!ctx) throw new Error(`Call ${num} not found`);
        const task = ctx.queue.shift();
        return this.actionMapper(task);
    }

    async startCall(to: string) {
        if (this.calls.has(to)) throw new Error(`Call ${to} already started`);
        const encodedTo = encodeURIComponent(to);
        const call = await this.client.calls.create({
            from: this.twilioNumber,
            to,
            statusCallback: `${this.streamUrl}/${encodedTo}/events`,
            twiml: `<Response>
                        <Connect>
                            <Stream url="${this.streamUrl}/${encodedTo}" />
                        </Connect>
                    </Response>`,
        });

        this.calls.set(to, {
            sid: call.sid,
            queue: []
        });
    }

    async enqueueAudio(num: string, url: string, immediate: boolean = false) {
        const ctx = this.calls.get(num);
        if (!ctx) throw new Error(`Call ${num} not found`);
        const task = { action: "play", url };
        if (immediate) {
            await this.client.calls(ctx.sid).update({
                twiml: this.actionMapper(task),
            });
        } else {
            ctx.queue.push(task);
        }
    }

    async pause(num: string, duration: number = 2, immediate: boolean = false) {
        const ctx = this.calls.get(num);
        if (!ctx) throw new Error(`Call ${num} not found`);
        const task = { action: "pause", duration: duration };
        if (immediate) {
            await this.client.calls(ctx.sid).update({
                twiml: this.actionMapper(task),
            });
        } else {
            ctx.queue.push(task);
        }
    }

    async hangup(num: string, immediate: boolean = false): Promise<void> {
        if (!this.calls.has(num)) return;
        const task = { action: "hangup" };
        if (immediate) {
            await this.client.calls(num).update({
                twiml: this.actionMapper(task),
            });
        } else {
            const ctx = this.calls.get(num);
            if (!ctx) throw new Error(`Call ${num} not found`);
            ctx.queue.push(task);
        }
        this.calls.delete(num);
    }

    private actionMapper(task: AudioTask | undefined): string {
        if (!task) return `
                <Response>
                    <Pause length="2" />
                    <Redirect>/next-instructions</Redirect>
                </Response>`;
        if (task.action === "play" && task.url)
            return `
                <Response>
                    <Play>${task.url}</Play>
                    <Redirect>/next-instructions</Redirect>
                </Response>
            `;
        if (task.action === "pause")
            return `
                <Response>
                    <Pause length="${task.duration ?? 2}" />
                    <Redirect>/next-instructions</Redirect>
                </Response>
            `;
        if (task.action === "hangup")
            return `
                <Response>
                    <Hangup />
                </Response>
            `;
        throw new Error(`Invalid task ${task}`);
    }
}
