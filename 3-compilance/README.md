# Design notes on compilance

## Do Not Disturb (DND) / Do Not Call (DNC)

- Check enable time ranges restrictions, we can define a db of rules that drives the behavior
- Track how many times we call a number in a period of time to avoid spam calls
- Use provided DND flag and settings for phone calls from lead event
    - Optionally we can define a store to keep it permanently or set a ttl
- As Secondary option we can also use public available DND/DNC lists
- Start witg a greeting that informs who is calling and tries to consent the call
- We could define a pipeline to allow cutomers to opt out during the call

## Protected Health Information (PHI)

- A supervisor agent can help on mantaining the boundaries of the conversation
- A custom memory agent could be in charge of mantaining the conversation context and discerning which information to gather
- We can use an agent and tools to collect only specific client information prior moving to next state
- There are no persisted info other than phone numbers and flags (out of memory I mean) but an encryption with priv/public certs can be implemented as needed


## Escalation & Safety

- We will store red flags in to a db and allow the agent to use them to determine if escalation is needed
    - This can be done exposing it as a tool
    - As a process that process the flags in to a vector database
    - Using an specilized/trained agent
- When escalation is needed we imediatelly redirects the flow to transfer the call using twilio conference
- Then we use an agent to create a brief and a presentation for the receptionist
- As in other cases we can use a Supervisor agent to prevent AI providing clinical advice.
    - Also this must be stated in the system promt for the agents that generates text that will be sent to the client.