from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

# Collections
leads_collection = db.leads
sessions_collection = db.sessions
calls_collection = db.calls

# Test connection (optional)
try:
    client.admin.command('ping')
    print("✅ MongoDB connected successfully")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
