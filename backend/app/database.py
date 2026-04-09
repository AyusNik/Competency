from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncIOMotorClient(os.getenv("MONGO_URI"))

# CAT system database
db = client[os.getenv("DB_NAME")]

# ILearn platform database (separate)
ilearn_db = client[os.getenv("ILEARN_DB_NAME")]
