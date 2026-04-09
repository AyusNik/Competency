from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import bcrypt, os
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "cat_secret_key")
ALGORITHM = "HS256"

_mypcp_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
mypcp_db = _mypcp_client["mypcp_db"]

router = APIRouter(prefix="/auth", tags=["Auth"])


class AuthRequest(BaseModel):
    name: str = ""
    email: str
    password: str
    manager_title: str = ""
    manager_phone: str = ""


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: str, name: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode({"sub": user_id, "name": name, "email": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
async def register(req: AuthRequest):
    existing = await db.managers.find_one({"email": req.email})
    if existing:
        raise HTTPException(400, "Email already registered")
    hashed = hash_password(req.password)
    result = await db.managers.insert_one({
        "name": req.name,
        "email": req.email,
        "password": hashed,
        "manager_title": req.manager_title,
        "manager_phone": req.manager_phone,
    })
    # Sync to mypcp_db.manager_pool so new MyPCP users get auto-assigned
    await mypcp_db.manager_pool.update_one(
        {"manager_email": req.email},
        {"$set": {
            "manager_name": req.name,
            "manager_email": req.email,
            "manager_phone": req.manager_phone,
            "manager_title": req.manager_title,
        }},
        upsert=True
    )
    token = create_token(str(result.inserted_id), req.name, req.email)
    return {"access_token": token, "name": req.name, "email": req.email}


@router.post("/login")
async def login(req: AuthRequest):
    user = await db.managers.find_one({"email": req.email})
    if not user or not verify_password(req.password, user["password"]):
        raise HTTPException(401, "Invalid email or password")
    token = create_token(str(user["_id"]), user["name"], user["email"])
    return {"access_token": token, "name": user["name"], "email": user["email"]}
