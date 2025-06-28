# db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()  # load .env

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "hexacare")

if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in environment variables")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]  # ✅ this is what you should import
