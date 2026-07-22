"""
Seed demo certifications for all users in mypcp_db.
Creates three certification types: ilearn, xylem, cbt.
"""
import asyncio
from datetime import date, timedelta
import hashlib

from motor.motor_asyncio import AsyncIOMotorClient


CERT_POOL = [
    {
        "certification_name": "TCC Essentials",
        "certification_type": "cbt",
        "certification_category": "function",
        "validity_status": "expired",
        "expires_on": None,
        "provider": "CBT Portal",
        "description": "Classroom training validation required.",
    },
    {
        "certification_name": "Malaria Prevention for Non-immunes",
        "certification_type": "ilearn",
        "certification_category": "generic",
        "validity_status": "expired",
        "expires_on": None,
        "provider": "iLearn",
        "description": "Mandatory generic certification.",
    },
    {
        "certification_name": "HSE Induction",
        "certification_type": "xylem",
        "certification_category": "local",
        "validity_status": "valid",
        "expires_on": (date.today() + timedelta(days=365)).isoformat(),
        "provider": "Xylem",
        "description": "Local onboarding certification.",
    },
    {
        "certification_name": "Workstation Safety",
        "certification_type": "ilearn",
        "certification_category": "learning",
        "validity_status": "expired",
        "expires_on": None,
        "provider": "iLearn",
        "description": "Safety awareness learning.",
    },
    {
        "certification_name": "Permit to Work Basics",
        "certification_type": "cbt",
        "certification_category": "function",
        "validity_status": "valid",
        "expires_on": (date.today() + timedelta(days=220)).isoformat(),
        "provider": "CBT Portal",
        "description": "PTW classroom certification.",
    },
    {
        "certification_name": "Driving Safety and Compliance",
        "certification_type": "xylem",
        "certification_category": "local",
        "validity_status": "valid",
        "expires_on": (date.today() + timedelta(days=540)).isoformat(),
        "provider": "Xylem",
        "description": "Local driving and fleet safety requirement.",
    },
    {
        "certification_name": "Incident Reporting Fundamentals",
        "certification_type": "ilearn",
        "certification_category": "generic",
        "validity_status": "pending",
        "expires_on": None,
        "provider": "iLearn",
        "description": "Generic incident reporting training.",
    },
    {
        "certification_name": "Radiation Awareness",
        "certification_type": "ilearn",
        "certification_category": "learning",
        "validity_status": "valid",
        "expires_on": (date.today() + timedelta(days=360)).isoformat(),
        "provider": "iLearn",
        "description": "Learning certification for radiation awareness.",
    },
]


def _pick_user_rows(user_id: str, user_name: str) -> list[dict]:
    """Pick a deterministic, user-specific subset from the shared certification pool."""
    # Deterministic index from user identity, so reseeding gives stable user-specific results.
    seed_hex = hashlib.sha256(f"{user_id}:{user_name}".encode()).hexdigest()
    base = int(seed_hex[:8], 16)

    # Each user gets 4..6 certifications.
    target_count = 4 + (base % 3)
    pool_size = len(CERT_POOL)

    picks = []
    used = set()
    offset = 0
    while len(picks) < target_count and len(used) < pool_size:
        idx = (base + (offset * 5)) % pool_size
        offset += 1
        if idx in used:
            continue
        used.add(idx)
        row = dict(CERT_POOL[idx])
        picks.append(row)

    # Ensure at least one CBT exists for validate-use-case testing.
    if not any(r.get("certification_type") == "cbt" for r in picks):
        cbt_row = next((dict(r) for r in CERT_POOL if r.get("certification_type") == "cbt"), None)
        if cbt_row:
            picks[0] = cbt_row

    return picks


async def seed():
    client = AsyncIOMotorClient("mongodb+srv://ayushnik:ayushnik@cluster0.zaiqzr7.mongodb.net/?appName=Cluster0")
    db = client["mypcp_db"]

    users = await db.users.find().to_list(1000)
    if not users:
        print("No users found. Register users first.")
        return

    total = 0
    for user in users:
        user_id = str(user["_id"])
        user_name = user.get("name", "")
        await db.certifications.delete_many({"user_id": user_id})
        chosen = _pick_user_rows(user_id, user_name)
        rows = [{"user_id": user_id, **item} for item in chosen]
        if rows:
            await db.certifications.insert_many(rows)
            total += len(rows)

    print(f"Seeded {total} certifications across {len(users)} users.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
