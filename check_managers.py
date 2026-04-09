import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run():
    db = AsyncIOMotorClient('mongodb://localhost:27017')['mypcp_db']
    
    print("=== USERS ===")
    users = await db.users.find().to_list(100)
    for u in users:
        print(f"  _id: {u['_id']}  name: {u['name']}")
    
    print("\n=== USER_MANAGERS ===")
    mgrs = await db.user_managers.find().to_list(100)
    for m in mgrs:
        print(f"  user_id: {m.get('user_id')}  manager: {m.get('manager_name')}")

asyncio.run(run())
