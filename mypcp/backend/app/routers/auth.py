from fastapi import APIRouter, HTTPException
from app.database import db
from app.models import UserCreate, UserLogin
from app.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["Auth"])


async def _auto_assign_manager(user_id: str):
    """Assign a manager to the new user using round-robin from manager_pool."""
    managers = await db.manager_pool.find().to_list(100)
    if not managers:
        return
    total_users = await db.users.count_documents({})
    manager = managers[total_users % len(managers)]
    await db.user_managers.insert_one({
        "user_id": user_id,
        "manager_name": manager["manager_name"],
        "manager_email": manager["manager_email"],
        "manager_phone": manager["manager_phone"],
        "manager_title": manager["manager_title"],
    })


@router.post("/register", status_code=201)
async def register(data: UserCreate):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(400, "Email already registered")
    user = {
        "name": data.name,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "job_title": data.job_title or "",
    }
    result = await db.users.insert_one(user)
    user_id = str(result.inserted_id)
    await db.user_competency_mappings.insert_one({
        "user_id": user_id,
        "competency_names": ["DSA"]
    })
    await _auto_assign_manager(user_id)
    token = create_token(user_id, data.name, data.email)
    return {"access_token": token, "token_type": "bearer", "name": data.name, "job_title": data.job_title}


@router.post("/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    user_id = str(user["_id"])
    token = create_token(user_id, user["name"], user["email"])
    return {"access_token": token, "token_type": "bearer", "name": user["name"], "job_title": user.get("job_title", "")}
