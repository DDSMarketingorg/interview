# AI Voice Assistant Architecture

## System Overview

The AI Voice Assistant for dental marketing is designed to automatically qualify leads from GoHighLevel (GHL) through intelligent phone conversations. The system follows a streamlined flow from lead receipt to appointment booking or qualification updates.

## Architecture Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│ GoHighLevel │───▶│   FastAPI   │───▶│   Twilio    │───▶│ AI Pipeline │
│  (Webhook)  │    │   Backend   │    │   Voice     │    │ (STT/LLM/   │
│             │    │             │    │   API       │    │    TTS)     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │                   ▼                   │                   │
       │            ┌─────────────┐            │                   │
       │            │             │            │                   │
       │            │  Database   │            │                   │
       │            │ (Postgres)  │            │                   │
       │            │             │            │                   │
       │            └─────────────┘            │                   │
       │                   │                   │                   │
       │                   ▼                   │                   │
       │            ┌─────────────┐            │                   │
       │            │    Redis    │            │                   │
       │            │  (Session   │            │                   │
       │            │ Management) │            │                   │
       │            └─────────────┘            │                   │
       │                                       │                   │
       └───────────────────────────────────────┼───────────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ GoHighLevel │
                                        │   Update    │
                                        │   (Notes/   │
                                        │Appointment) │
                                        └─────────────┘
```

## Component Details

### 1. FastAPI Backend (`src/main.py`)
- **Purpose**: Central orchestrator for all system components
- **Responsibilities**:
  - Receive and validate GHL webhooks
  - Manage call sessions and state
  - Coordinate AI pipeline components
  - Handle compliance checks (DNC, PHI)
  - Update lead status in GHL

### 2. Webhook Handler (`src/services/webhook_service.py`)
- **Purpose**: Process incoming lead notifications from GHL
- **Key Features**:
  - Webhook signature validation
  - DNC list checking
  - Lead data extraction and validation
  - Call scheduling and initiation

### 3. Twilio Voice Service (`src/services/twilio_service.py`)
- **Purpose**: Manage voice communications
- **Capabilities**:
  - Outbound call initiation
  - Dynamic TwiML generation
  - Call status monitoring
  - Real-time audio streaming for AI processing

### 4. AI Conversation Pipeline (`src/services/ai_service.py`)
- **Components**:
  - **STT (Speech-to-Text)**: OpenAI Whisper API
  - **LLM (Language Model)**: GPT-4o with structured prompts
  - **TTS (Text-to-Speech)**: AWS Polly for natural voice synthesis
- **Features**:
  - Context-aware conversation flow
  - Structured data extraction
  - Emergency escalation detection
  - Compliance monitoring

### 5. GHL Integration Service (`src/services/ghl_service.py`)
- **Purpose**: Bidirectional communication with GoHighLevel
- **Functions**:
  - Lead data retrieval
  - Contact updates (notes, tags, stage)
  - Appointment creation
  - Custom field updates

### 6. Data Models (`src/models/`)
- **Lead Model**: Contact information and preferences
- **Call Session Model**: Conversation state and history
- **Qualification Model**: Structured lead qualification data
- **Compliance Model**: DNC status and PHI handling flags

## Data Flow

### Phase 1: Lead Receipt
1. GHL sends webhook with new lead data
2. System validates webhook signature
3. Lead is checked against DNC list
4. If eligible, call is scheduled

### Phase 2: Call Initiation
1. Twilio initiates outbound call
2. Dynamic TwiML connects call to AI pipeline
3. Session state is created in Redis
4. Initial greeting is played via TTS

### Phase 3: AI Conversation
1. Customer speech is captured and converted to text (STT)
2. LLM processes conversation context and generates response
3. Response is converted to speech (TTS) and played
4. Structured data is extracted throughout conversation
5. Emergency conditions trigger immediate escalation

### Phase 4: Data Update
1. Conversation results are structured into qualification data
2. Lead record is updated in GHL with:
   - Qualification notes
   - Pain level and urgency
   - Insurance information
   - Preferred appointment slots
3. Appointment is scheduled if appropriate

## Scalability Considerations

### Horizontal Scaling
- Stateless FastAPI instances behind load balancer
- Redis for shared session state
- Database connection pooling

### Performance Optimization
- Async/await patterns for concurrent call handling
- Connection pooling for external APIs
- Caching for frequent GHL API calls

### Monitoring & Observability
- Call quality metrics
- Conversation success rates
- Response time monitoring
- Error tracking and alerting

## Security Architecture

### Data Protection
- End-to-end encryption for PHI
- Secure credential management via environment variables
- Database encryption at rest
- TLS for all API communications

### Access Control
- API key authentication for GHL webhooks
- JWT tokens for internal service communication
- Rate limiting and DDoS protection
- Audit logging for all patient interactions

## Compliance Framework

### HIPAA Compliance
- Minimal data collection principles
- Secure data transmission protocols
- Access logging and audit trails
- Data retention policies

### Telecommunications Compliance
- DNC list integration and checking
- Call recording consent (where required)
- Opt-out mechanisms
- Time-of-day calling restrictions

## Deployment Architecture

### Development Environment
- Docker containers for consistent development
- Environment-specific configuration
