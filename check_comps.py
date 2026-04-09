import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['cat_db']
    comps = await db.competencies.find().to_list(100)
    for c in comps:
        print(c)

asyncio.run(run())
