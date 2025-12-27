# from flask import Flask
from flask_cors import CORS
import base64
from routes.ghl import ghl_bp
from routes.voice import voice_bp
import io
from pydub import AudioSegment
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from services.escalation import build_human_reply, check_escalation, extract_insurance_fallback, extract_preferred_slot, next_agent_reply
from services.llm_service import  run_llm
from services.sessions_service import get_session, is_confirmation, merge_session_data
from services.socket_handlers import register_socket_events
import openai
import os
from faster_whisper import WhisperModel
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
register_socket_events(socketio)

app.register_blueprint(ghl_bp)
app.register_blueprint(voice_bp)



openai.api_key = os.environ.get("OPENAI_API_KEY")
@socketio.on("user_text")
def handle_user_text(data):
    user_text = data["text"]
    print("🎤 User:", user_text)

    if not user_text:
        emit("ai_text", {"text": "I didn't receive any input."}, to=request.sid)
        return

    # -------- LLM --------
    #  استفاده از GPT-4o برای استخراج structured data
    session = get_session(request.sid)

    if session["state"] == "AWAITING_CONFIRMATION" and is_confirmation(user_text):
        session["state"] = "BOOKED"
        emit("ai_text", {
            "text": "Perfect. Your appointment has been scheduled. See you soon!"
        })
        return

    structured_data  = run_llm(user_text)
    print("🧠 structured_data :", structured_data)
    if not structured_data.get("insurance_provider"):
        insurance = extract_insurance_fallback(user_text)
        if insurance:
            structured_data["insurance_provider"] = insurance

    if not structured_data.get("preferred_slot"):
        slot = extract_preferred_slot(user_text)
        if slot:
            structured_data["preferred_slot"] = slot

    merge_session_data(session["data"], structured_data)
    # print("🧠 SESSION DATA:", session["data"])
    # print("📌 STATE:", session["state"])

    needs_human, reason = check_escalation(structured_data)
    if needs_human:
        emit("ai_text", {
            "text": (
                "I’m not able to help further with this. "
                "I’m transferring you to a human receptionist now."
            )
        })
        emit("handoff", {
            "reason": reason,
            "structured_data": structured_data
        })
        return
    # -------- Send response back to browser --------
    reply = next_agent_reply(session)
    emit("ai_text", {"text": reply}, to=request.sid)
    # -------------------------------------------------------

    # -------- Optional: save to DB / GHL --------
    # save_session(user_id, structured_data)



@app.route('/')
def index():
    return render_template('voice.html', lead_id="CNT_xxx")  # UI با دکمه

if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
    )

