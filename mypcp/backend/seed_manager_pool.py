import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MANAGERS = [
    {
        "manager_name": "Kratika Nenwani",
        "manager_email": "kratika.nenwani@capgemini.com",
        "manager_phone": "+91 9198754333",
        "manager_title": "Business Line Manager — DSA & Engineering",
    },
]

async def seed():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["mypcp_db"]
    await db.manager_pool.delete_many({})
    await db.manager_pool.insert_many(MANAGERS)
    print(f"Seeded {len(MANAGERS)} manager(s) into manager_pool.")
    client.close()

asyncio.run(seed())
