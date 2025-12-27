from flask import Blueprint, request, jsonify
from db.mongo import leads_collection
from services.twilio_service import activate_voice_agent
from datetime import datetime
from db.mongo import sessions_collection

ghl_bp = Blueprint("ghl", __name__)

@ghl_bp.route("/webhook/ghl", methods=["POST"])
def ghl_webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "invalid payload"}), 400
       

        event = data.get("event")
        contact = data.get("contact", {})
        # فقط لید جدید
        if event != "contact.created":
            return jsonify({"status": "ignored", "event": event}), 200
        lead_data = {
            "contact_id": contact.get("id"),
            "first_name": contact.get("firstName"),
            "phone": contact.get("phone"),
            "email": contact.get("email")
        }
        session_doc = {
            "lead_data": lead_data,
            "lead_id": lead_data["contact_id"],
            "active": False,        # Voice Agent هنوز فعال نشده
            "created_at": datetime.utcnow(),
            "audio_chunks": [],     # برای ذخیره موقتی صدا (اختیاری)
            "results": []           # structured data استخراج شده
        }
        
        existing = sessions_collection.find_one({"lead_id": lead_data["contact_id"]})
        if existing:
            return jsonify({
                "status": "error",
                "message": f"Lead with lead_id {lead_data['contact_id']} already exists"
            }), 400

        sessions_collection.insert_one(session_doc)
        return jsonify({
            "message": "session created for lead",
            "lead_id": session_doc["lead_id"]
        }), 200



        # result = leads_collection.insert_one({
        #     "contact_id": contact_id,
        #     "firstName": first_name,
        #     "phone": phone,
        #     "email": email,
        #     "created_at": datetime.utcnow()
        # })

        # تماس با Twilio
        # call_sid = make_call(phone, str(result.inserted_id))


    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
