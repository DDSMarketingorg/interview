from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from db.mongo import sessions_collection

app = Flask(__name__)
socketio = SocketIO(app)

def get_session(lead_id: str) -> dict:
   
    session = sessions_collection.find_one({"lead_id": lead_id})
    if session:
        return session
    else:
        return None

# @socketio.on("activate_voice_agent")
# def handle_activate_voice_agent(data=None):
#     # lead_id = data["lead_id"]
#     print("ggggggggggggggggg")
#     result = sessions_collection.update_one(
#         {"lead_id": "CNT_xxx"},
#         {"$set": {"active": True}}
#     )
#     if result.matched_count == 0:
#         emit("error", {"message": "session not found"})
#         return

#     # emit("agent_activated", {"lead_id": lead_id})
#     emit("agent_activated", {"lead_id": "CNT_xxx"})




# @socketio.on("audio_chunk")
# def handle_audio_chunk(data):
#     lead_id = data["lead_id"]
#     audio_chunk = data["audio"]
#     text = stt(audio_chunk)       # Whisper یا mock
#     structured_data = run_llm(text)
#     audio_response = tts(structured_data)
#     emit("tts_chunk", audio_response)