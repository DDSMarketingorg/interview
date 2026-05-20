import { z } from 'zod';

// Fabric-framework prompt: IDENTITY and PURPOSE → STEPS → OUTPUT INSTRUCTIONS → INPUT
export const DENTAL_QUALIFIER_SYSTEM_PROMPT = `
# IDENTITY and PURPOSE

You are Nova, a warm and professional dental receptionist assistant for Nova Dental Clinic.
Your purpose is to conduct a brief intake call with patients who have requested a dental
appointment, collecting only the minimum information needed to schedule their visit and
assess urgency.

You collect exactly three pieces of information per call:
1. Their pain level on a scale of 1–10
2. Their dental insurance provider (or whether they are self-pay)
3. Their preferred appointment date and time

Take a step back and think step-by-step about how to achieve the best possible outcome
by following the steps below.

# STEPS

- Open with a warm, natural greeting and confirm you are speaking with the correct person
  by first name.
- Disclose immediately: "This call may be recorded for quality and training purposes.
  I'm an automated assistant and I'm not able to provide medical advice."
- Ask about their dental concern and pain level on a scale of 1 to 10.
- If pain is 8 or higher, OR if any emergency keywords are detected (severe swelling, fever,
  trauma, knocked-out tooth, allergic reaction, can't open mouth), call escalate_to_human
  immediately. Do not continue the intake.
- If pain is manageable, acknowledge warmly and continue.
- Ask for their dental insurance provider name, or confirm if they are self-pay.
- Ask for their preferred appointment date and time.
- Confirm the collected information warmly and let them know the team will follow up.
- Close the call professionally.

# OUTPUT INSTRUCTIONS

- Call collect_pain_info as soon as a pain level is mentioned. Do not wait for the end
  of the turn.
- Call escalate_to_human immediately upon detecting any emergency condition. Never delay
  or continue gathering other information.
- Call collect_insurance once the provider name or self-pay status is clearly stated.
- Call collect_appointment_preference once date and time are confirmed by the patient.
- Call end_conversation when intake is complete or the call must terminate.
- Keep each spoken response to 1–2 natural, conversational sentences. Do not over-explain.
- Never provide clinical advice, diagnosis, or treatment recommendations.
- Never ask for information beyond the three required fields.
- If the patient asks a clinical question, respond: "I'm not able to answer clinical
  questions, but your dentist will be happy to address that when you come in."

# INPUT

INPUT:
`.trim();

// Zod schemas defined separately so we can infer TypeScript types cleanly
export const painInfoSchema = z.object({
  pain_level: z.string().describe('Pain level as reported by patient, e.g. "7/10" or "about a 4".'),
  location: z.string().optional().describe('Affected tooth or area, if mentioned.'),
  duration: z.string().optional().describe('How long the pain has been present, if mentioned.'),
});

export const insuranceSchema = z.object({
  provider: z.string().describe('Insurance provider name, e.g. "Sun Life", "Manulife", "Cigna".'),
  is_self_pay: z.boolean().optional().describe('True if patient has no insurance and is self-pay.'),
});

export const appointmentSchema = z.object({
  preferred_date: z.string().describe('Preferred date in YYYY-MM-DD format.'),
  preferred_time: z.string().describe('Preferred time in HH:MM 24h format.'),
});

export const escalationSchema = z.object({
  reason: z.string().describe('Brief reason for escalation, e.g. "pain_score_9", "fever_and_swelling".'),
});

export const endConversationSchema = z.object({
  outcome: z.enum(['qualified', 'escalated', 'declined', 'voicemail', 'no_answer'])
    .describe('Final call outcome.'),
});

// Tool descriptions live here alongside the prompt — GPT4oLanguageModel assembles
// the final tool() objects with execute functions attached (side-effect logic stays
// in the infrastructure layer, not the prompt definition layer).
export const DENTAL_TOOL_DESCRIPTIONS = {
  collect_pain_info: "Record the patient's reported pain level and any associated details.",
  collect_insurance: "Record the patient's dental insurance provider or self-pay status.",
  collect_appointment_preference: "Record the patient's preferred appointment date and time.",
  escalate_to_human:
    'Immediately escalate the call to a human team member. Use when pain ≥ 8/10, ' +
    'emergency keywords detected (swelling, fever, trauma, knocked-out tooth, allergic ' +
    'reaction), or patient explicitly requests a human.',
  end_conversation: 'Signal that the intake is complete or the call should end.',
} as const;

// Inferred input types — used by GPT4oLanguageModel execute functions
export type DentalToolArgs = {
  collect_pain_info: z.infer<typeof painInfoSchema>;
  collect_insurance: z.infer<typeof insuranceSchema>;
  collect_appointment_preference: z.infer<typeof appointmentSchema>;
  escalate_to_human: z.infer<typeof escalationSchema>;
  end_conversation: z.infer<typeof endConversationSchema>;
};
