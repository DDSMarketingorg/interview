

[GoHighLevel] 
      │
      │ Webhook (New Lead)
      ▼
[Flask Backend] ────► [MongoDB]  (ذخیره اطلاعات)
      │
      │ Send Audio to AI Pipeline
      ▼
[AI Pipeline: STT → LLM → TTS] 
      │
      │ Generate Response
      ▼
[Flask Backend] ───► Update Lead in GHL / Database
