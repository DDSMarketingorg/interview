1. Patient Data & Privacy
    No PHI storage 

    Audio deleted after processing

    No patient data is persisted beyond the call lifecycle

2. HIPAA Awareness (Design-Level)

    AI is used strictly for conversational assistance, not diagnosis.

    No medical advice or treatment recommendations are generated.

    Escalation to a human receptionist is triggered for:

    Urgent symptoms

    Ambiguous or high-risk responses

3. Third-Party APIs
    Voice and AI providers are treated as processors, not data owners.

    API keys and secrets are stored using environment variables.

    The architecture allows swapping providers without core logic changes.

---------------------------------------------------------
Design Decisions
1. Deterministic State Machine over Free-form AI

    Why:
    AI responses can be unpredictable.

    Decision:
    LLM is only used for:
        Extracting structured fields
        Classifying urgency
        Conversation flow is controlled by a deterministic state machine.

    Benefit:
        Predictable behavior
        Easier debugging
        Production safety


2. Insurance Is Non-Blocking

    Why:
        Patients without insurance should still be able to book.

    Decision:
        Insurance status is collected but never blocks scheduling.
        Self-pay logic is informational only.


3. Escalation-First Safety Model

    Why:
        Healthcare calls can become critical.

    Decision:

        Any uncertainty, emotional distress, or urgent symptoms trigger escalation.
        The AI never attempts to resolve emergencies.


4. Modular AI Pipeline

    Why:
        Future extensibility.

    Decision:
        STT, LLM, and TTS are independent modules.
        Each component can be replaced without refactoring the entire system.



5. Real-Time Interaction via WebSockets

    Why:
        Voice agents require low latency.

        Decision:

        WebSockets are used for:

        Streaming user input

        Incremental AI responses

        Enables near real-time conversational experience.