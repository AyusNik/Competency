"""
Seed user_managers collection in mypcp_db.
Assigns a default manager to all existing users.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MANAGERS = [
    {
        "manager_name": "Sarah Mitchell",
        "manager_email": "sarah.mitchell@company.com",
        "manager_phone": "+1-555-0142",
        "manager_title": "Business Line Manager — DSA & Engineering",
    },
    {
        "manager_name": "James Okafor",
        "manager_email": "james.okafor@company.com",
        "manager_phone": "+1-555-0198",
        "manager_title": "Business Line Manager — Core Competencies",
    },
]


async def seed():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["mypcp_db"]

    users = await db.users.find().to_list(100)
    if not users:
        print("No users found in mypcp_db — register a user first then re-run.")
        return

    for i, user in enumerate(users):
        user_id = str(user["_id"])
        existing = await db.user_managers.find_one({"user_id": user_id})
        if existing:
            print(f"Manager already assigned to {user['name']}, skipping.")
            continue
        mgr = MANAGERS[i % len(MANAGERS)]
        await db.user_managers.insert_one({"user_id": user_id, **mgr})
        print(f"Assigned '{mgr['manager_name']}' as manager for {user['name']}")

    print("Done.")


asyncio.run(seed())
