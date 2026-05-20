import { MigrationInterface, QueryRunner } from 'typeorm';

export class InitialSchema1720000000000 implements MigrationInterface {
  name = 'InitialSchema1720000000000';

  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      CREATE EXTENSION IF NOT EXISTS "pgcrypto";

      CREATE TABLE "leads" (
        "id"               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "ghl_contact_id"   VARCHAR NOT NULL,
        "first_name"       VARCHAR NOT NULL,
        "phone"            VARCHAR NOT NULL,
        "email"            VARCHAR,
        "created_at"       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT "uq_leads_ghl_contact_id" UNIQUE ("ghl_contact_id")
      );

      CREATE TABLE "lead_dnc" (
        "id"           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "lead_id"      UUID NOT NULL,
        "is_dnc"       BOOLEAN NOT NULL DEFAULT FALSE,
        "dnc_set_at"   TIMESTAMPTZ,
        "dnc_reason"   VARCHAR,
        CONSTRAINT "uq_lead_dnc_lead_id" UNIQUE ("lead_id"),
        CONSTRAINT "fk_lead_dnc_lead" FOREIGN KEY ("lead_id") REFERENCES "leads" ("id") ON DELETE CASCADE
      );

      CREATE TYPE "call_status_enum" AS ENUM ('pending', 'active', 'completed', 'failed');

      CREATE TABLE "call_logs" (
        "id"               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "lead_id"          UUID NOT NULL,
        "twilio_call_sid"  VARCHAR NOT NULL,
        "status"           call_status_enum NOT NULL DEFAULT 'pending',
        "started_at"       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        "ended_at"         TIMESTAMPTZ,
        CONSTRAINT "uq_call_logs_call_sid" UNIQUE ("twilio_call_sid"),
        CONSTRAINT "fk_call_logs_lead" FOREIGN KEY ("lead_id") REFERENCES "leads" ("id") ON DELETE CASCADE
      );

      CREATE TABLE "call_escalations" (
        "id"           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "call_log_id"  UUID NOT NULL,
        "reason"       VARCHAR NOT NULL,
        "escalated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT "uq_call_escalations_call_log" UNIQUE ("call_log_id"),
        CONSTRAINT "fk_call_escalations_call_log" FOREIGN KEY ("call_log_id") REFERENCES "call_logs" ("id") ON DELETE CASCADE
      );

      CREATE TYPE "transcript_role_enum" AS ENUM ('user', 'assistant');

      CREATE TABLE "transcripts" (
        "id"           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "call_log_id"  UUID NOT NULL,
        "role"         transcript_role_enum NOT NULL,
        "content"      TEXT NOT NULL,
        "turn_index"   INT NOT NULL,
        "timestamp"    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT "fk_transcripts_call_log" FOREIGN KEY ("call_log_id") REFERENCES "call_logs" ("id") ON DELETE CASCADE
      );

      CREATE INDEX "idx_transcripts_call_log_id" ON "transcripts" ("call_log_id");

      CREATE TYPE "field_name_enum" AS ENUM ('pain_level', 'insurance_provider', 'preferred_slot');

      CREATE TABLE "collected_fields" (
        "id"            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        "call_log_id"   UUID NOT NULL,
        "field_name"    field_name_enum NOT NULL,
        "field_value"   VARCHAR NOT NULL,
        "collected_at"  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT "uq_collected_fields_call_field" UNIQUE ("call_log_id", "field_name"),
        CONSTRAINT "fk_collected_fields_call_log" FOREIGN KEY ("call_log_id") REFERENCES "call_logs" ("id") ON DELETE CASCADE
      );

      CREATE INDEX "idx_collected_fields_call_log_id" ON "collected_fields" ("call_log_id");
    `);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      DROP TABLE IF EXISTS "collected_fields";
      DROP TABLE IF EXISTS "transcripts";
      DROP TABLE IF EXISTS "call_escalations";
      DROP TABLE IF EXISTS "call_logs";
      DROP TABLE IF EXISTS "lead_dnc";
      DROP TABLE IF EXISTS "leads";
      DROP TYPE IF EXISTS "field_name_enum";
      DROP TYPE IF EXISTS "transcript_role_enum";
      DROP TYPE IF EXISTS "call_status_enum";
    `);
  }
}
