from flask import Blueprint, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse
from db.mongo import leads_collection
from services.stt_service import speech_to_text
from bson import ObjectId

from services.tts_service import text_to_speech
voice_bp = Blueprint("voice", __name__)

# @voice_bp.route("/voice/answer", methods=["POST"])
# def voice_answer():
#     vr = VoiceResponse()
#     vr.say("Hello, this is a dental assistant. How can I help you?")
#     vr.record(
#         action="https://fa5e541643dc94.lhr.life/voice/process",
#         timeout=5,
#         play_beep=True
#     )
#     return Response(str(vr), mimetype="text/xml")


# @voice_bp.route("/process", methods=["POST"])
# def process_speech():
#     # RecordingUrl -> STT -> LLM -> TTS
#     vr = VoiceResponse()
#     vr.say("Thank you. We will contact you soon.")
#     return Response(str(vr), mimetype="text/xml")

@voice_bp.route("/mock-voice", methods=["POST"])
def mock_voice():
    return jsonify({
        "transcript": "I have tooth pain",
        "ai_response": "Thanks, we will schedule an appointment for you."
    })

@voice_bp.route("/voice/answer/<lead_id>", methods=["POST"])
def answer_call(lead_id):
    # Twilio initial response: greet user and record
    vr = VoiceResponse()
    vr.say("Hello, this is your dental assistant. Please tell me about your dental issue.")
    vr.record(
        action=f"/voice/process/{lead_id}",
        timeout=5,
        play_beep=True
    )
    return Response(str(vr), mimetype="text/xml")

# @voice_bp.route("/process/<lead_id>", methods=["POST"])
# def process_recording(lead_id):
#     # Twilio recording URL
#     recording_url = request.form.get("RecordingUrl")

#     # 1️⃣ Mock STT
#     user_text = speech_to_text(recording_url)

#     # 2️⃣ Mock LLM
#     # structured_info = generate_response(user_text)

#     # 3️⃣ Update lead in MongoDB
#     leads_collection.update_one(
#         {"_id": ObjectId(lead_id)},
#         {"$set": {
#             "status": "contacted",
#             "pain": structured_info["pain"],
#             "preferred_day": structured_info["preferred_day"],
#             "appointment_confirmed": structured_info["appointment_confirmed"]
#         }}
#     )

#     # 4️⃣ Mock TTS response
#     ai_message = structured_info["ai_message"]
#     text_to_speech(ai_message)

#     # 5️⃣ Respond to Twilio
#     vr = VoiceResponse()
#     vr.say(ai_message)
#     vr.hangup()
#     return Response(str(vr), mimetype="text/xml")
