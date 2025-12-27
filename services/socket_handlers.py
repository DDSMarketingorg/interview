from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from db.mongo import sessions_collection

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on("audio_chunk")
def handle_audio(data):
    audio_blob = data["audio"]
    print("🎤 received audio chunk", audio_blob)

def register_socket_events(socketio):
    @socketio.on("activate_voice_agent")
    def handle_activate_voice_agent(data=None):
        # lead_id = data["lead_id"]
        
        result = sessions_collection.update_one(
            {"lead_id": "CNT_xxx"},
            {"$set": {"active": True}}
        )
        if result.matched_count == 0:
            emit("error", {"message": "session not found"})
            return

        # emit("agent_activated", {"lead_id": lead_id})
        emit("agent_activated", {"lead_id": "CNT_xxx"})
