import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    db = AsyncIOMotorClient('mongodb://localhost:27017')['mypcp_db']
    result = await db.chat_sessions.delete_many({})
    print(f"Cleared {result.deleted_count} chat session(s)")

asyncio.run(run())
