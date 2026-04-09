from fastapi import APIRouter, HTTPException
from app.database import db
from app.models.models import PLRModel
from bson import ObjectId

router = APIRouter(prefix="/plr", tags=["PLR"])


def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/")
async def get_all():
    return [serialize(c) async for c in db.plr.find()]


@router.get("/{id}")
async def get_one(id: str):
    doc = await db.plr.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(404, "Not found")
    return serialize(doc)


@router.post("/", status_code=201)
async def create(data: PLRModel):
    result = await db.plr.insert_one(data.model_dump(exclude={"id"}))
    return {"id": str(result.inserted_id)}


@router.put("/{id}")
async def update(id: str, data: PLRModel):
    await db.plr.update_one({"_id": ObjectId(id)}, {"$set": data.model_dump(exclude={"id"})})
    return {"updated": True}


@router.delete("/{id}")
async def delete(id: str):
    await db.plr.delete_one({"_id": ObjectId(id)})
    return {"deleted": True}
