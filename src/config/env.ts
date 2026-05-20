import 'dotenv/config';
import { z } from 'zod';

const schema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  HOST: z.string().min(1),
  DATABASE_URL: z.string().url(),
  TWILIO_ACCOUNT_SID: z.string().startsWith('AC'),
  TWILIO_AUTH_TOKEN: z.string().min(1),
  TWILIO_NUMBER: z.string().startsWith('+'),
  GHL_WEBHOOK_SECRET: z.string().min(1),
  OPENAI_API_KEY: z.string().startsWith('sk-'),
  ELEVENLABS_API_KEY: z.string().min(1),
  ELEVENLABS_VOICE_ID: z.string().min(1),
  GHL_API_KEY: z.string().min(1),
  GHL_LOCATION_ID: z.string().min(1),
  GHL_CALENDAR_ID: z.string().min(1),
});

const parsed = schema.safeParse(process.env);
if (!parsed.success) {
  console.error('❌  Missing or invalid environment variables:');
  console.error(parsed.error.format());
  process.exit(1);
}

export const env = parsed.data;
