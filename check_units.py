import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['cat_db']
    units = await db.competency_units.find().to_list(10)
    for u in units:
        print(u)

asyncio.run(run())
