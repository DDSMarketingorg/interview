// reflect-metadata MUST be the very first import for TypeORM decorators to work
import 'reflect-metadata';
import './config/env'; // validates env vars at startup — exits if invalid

import express from 'express';
import rateLimit from 'express-rate-limit';
import { WebSocketServer } from 'ws';
import http from 'http';

import { env } from './config/env';
import { AppDataSource } from './infrastructure/database/typeorm/dataSource';

// Repositories
import { LeadRepository } from './infrastructure/database/repositories/LeadRepository';
import { CallLogRepository } from './infrastructure/database/repositories/CallLogRepository';
import { CollectedFieldsRepository } from './infrastructure/database/repositories/CollectedFieldsRepository';

// Providers
import { TwilioVoiceProvider } from './infrastructure/providers/TwilioVoiceProvider';
import { WhisperSpeechToText } from './infrastructure/providers/WhisperSpeechToText';
import { ElevenLabsTTS } from './infrastructure/providers/ElevenLabsTTS';
import { GPT4oLanguageModel } from './infrastructure/providers/GPT4oLanguageModel';
import { GHLGateway } from './infrastructure/providers/GHLGateway';

// Use cases
import { HandleInboundLeadUseCase } from './application/usecases/HandleInboundLeadUseCase';
import { ProcessVoiceTurnUseCase } from './application/usecases/ProcessVoiceTurnUseCase';
import { FinalizeCallUseCase } from './application/usecases/FinalizeCallUseCase';

// HTTP
import { GHLWebhookController } from './infrastructure/http/controllers/GHLWebhookController';
import { VoiceStreamController } from './infrastructure/http/controllers/VoiceStreamController';
import { hmacVerify } from './infrastructure/http/middleware/hmacVerify';
import { makeDncCheck } from './infrastructure/http/middleware/dncCheck';

async function bootstrap() {
  await AppDataSource.initialize();
  console.info('✅  Database connected');

  const leadRepo = new LeadRepository(AppDataSource);
  const callLogRepo = new CallLogRepository(AppDataSource);
  const collectedFieldsRepo = new CollectedFieldsRepository(AppDataSource);

  const voiceProvider = new TwilioVoiceProvider(env.TWILIO_ACCOUNT_SID, env.TWILIO_AUTH_TOKEN, env.TWILIO_NUMBER);
  const stt = new WhisperSpeechToText();
  const tts = new ElevenLabsTTS(env.ELEVENLABS_API_KEY, env.ELEVENLABS_VOICE_ID);
  const llm = new GPT4oLanguageModel();
  const ghlGateway = new GHLGateway(env.GHL_API_KEY, env.GHL_LOCATION_ID, env.GHL_CALENDAR_ID);

  const handleInboundLead = new HandleInboundLeadUseCase(
    leadRepo, callLogRepo, voiceProvider, ghlGateway, env.HOST,
  );
  const processVoiceTurn = new ProcessVoiceTurnUseCase(
    callLogRepo, collectedFieldsRepo, stt, tts, llm,
  );
  const finalizeCall = new FinalizeCallUseCase(
    callLogRepo, collectedFieldsRepo, leadRepo, ghlGateway,
  );

  const ghlWebhookController = new GHLWebhookController(handleInboundLead);
  const voiceStreamController = new VoiceStreamController(processVoiceTurn, finalizeCall);

  const app = express();
  app.use(express.json());

  app.get('/health', (_req, res) => res.json({ status: 'ok' }));

  app.post(
    '/webhooks/ghl',
    rateLimit({ windowMs: 60_000, max: 60, standardHeaders: true, legacyHeaders: false }),
    hmacVerify(env.GHL_WEBHOOK_SECRET),
    makeDncCheck(ghlGateway),
    (req, res, next) => void ghlWebhookController.handle(req, res, next),
  );

  app.use((err: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
    console.error('[Error]', err);
    res.status(500).json({ error: 'Internal server error' });
  });

  const server = http.createServer(app);
  const wss = new WebSocketServer({ server, path: '/voice/stream' });

  wss.on('connection', (ws) => {
    voiceStreamController.handle(ws);
  });

  server.listen(env.PORT, () => {
    console.info(`🚀  Server listening on port ${env.PORT}`);
    console.info(`    Webhook:    POST  /webhooks/ghl`);
    console.info(`    Voice WS:   WS    /voice/stream`);
  });
}

bootstrap().catch((err) => {
  console.error('Fatal startup error:', err);
  process.exit(1);
});
