import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['mypcp_db']
    result = await db.user_competency_mappings.update_many(
        {"competency_names": "Array"},
        {"$set": {"competency_names": ["DSA"]}}
    )
    print(f"Fixed {result.modified_count} mappings")
    # Also show all mappings now
    all_m = await db.user_competency_mappings.find().to_list(100)
    for m in all_m:
        print(m)

asyncio.run(run())
