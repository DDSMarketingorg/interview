# Compliance And Safety Notes

This document covers the production handling of DND / DNC controls, PHI minimization, and escalation behavior for the dental voice assistant workflow.

## DND / DNC

Before any outbound call attempt, the backend checks the contact record received from GoHighLevel for `DND` and `DNC` style suppression flags.

Expected behavior:

- If a lead is marked `DND` or `DNC`, the system does not place the outbound call.
- The lead is still stored so the office has an audit trail of the inbound request.
- The lead is marked as blocked or suppressed in the local system.
- The CRM can be updated with a note or stage indicating that outreach was skipped due to contact preferences.
- Retry logic must also respect these flags, not just the first call attempt.

Why this matters:

- It prevents avoidable compliance violations.
- It keeps automations from repeatedly attempting outreach after a lead has opted out.
- It gives office staff a clear explanation for why a lead was not contacted automatically.

## PHI Minimization

This workflow should collect only the minimum information needed to route or schedule the lead.

Data that is appropriate to collect:

- reason for contact or chief complaint
- pain level
- insurance provider
- preferred appointment time

Data that should be avoided unless absolutely necessary:

- detailed clinical history
- diagnosis-style conversations
- treatment recommendations
- extra medical data unrelated to scheduling or urgent routing

Storage expectations:

- Data should be encrypted in transit with HTTPS/TLS.
- Data stored in Postgres should be encrypted at rest using cloud-provider managed disk or database encryption.
- Backups, snapshots, and any replicated database storage should also inherit encryption at rest.
- Secrets such as API keys and database credentials should be stored in a secret manager or equivalent secure runtime configuration, not committed in source control.
- Access to transcripts and lead records should be restricted to authorized staff and system components.
- Retention should be limited to what the office actually needs for booking, follow-up, and auditability.

Operational note:

- The AI should not behave like a clinical charting tool.
- It should gather enough information to qualify the lead, then stop.

## Escalation And Safety

The assistant should immediately stop normal qualification and hand the lead off to a human if urgent symptoms are reported.

Red-flag examples:

- pain rated `8/10` to `10/10`
- swelling plus fever
- dental trauma
- broken or knocked-out tooth
- allergy concerns
- significant bleeding

Suggested production behavior:

- `10/10` pain or emergency-style symptoms trigger immediate escalation.
- `8/10` or `9/10` pain prompts a fast confirmation question about whether the caller wants immediate help.
- If the caller says yes, the call is transferred or routed for urgent human follow-up.
- The CRM is updated with an urgent note and visible stage/status marker.

Clinical safety boundary:

- The AI does not diagnose.
- The AI does not recommend treatment.
- The AI does not give medical advice.
- The AI only gathers intake information and routes the lead appropriately.

## Writeback Expectations

When the automated intake completes, the CRM writeback should be limited to operationally useful fields such as:

- qualification status
- scheduling stage
- structured intake values
- urgent handoff marker when applicable
- concise receptionist-style note

That keeps the CRM useful for follow-up while avoiding unnecessary storage of sensitive conversational detail.
