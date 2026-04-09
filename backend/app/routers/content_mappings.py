from fastapi import APIRouter, HTTPException, Query
from app.database import db
from app.models.models import ContentMappingModel
from bson import ObjectId
from typing import Optional

router = APIRouter(prefix="/content-mappings", tags=["Content Mappings"])


def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc


@router.get("/")
async def get_all(search: Optional[str] = Query(None)):
    query = {}
    if search:
        query = {"$or": [
            {"ce_unit": {"$regex": search, "$options": "i"}},
            {"competency_element": {"$regex": search, "$options": "i"}},
        ]}
    return [serialize(c) async for c in db.content_mappings.find(query)]


@router.get("/{id}")
async def get_one(id: str):
    doc = await db.content_mappings.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(404, "Not found")
    return serialize(doc)


@router.post("/", status_code=201)
async def create(data: ContentMappingModel):
    result = await db.content_mappings.insert_one(data.model_dump(exclude={"id"}))
    return {"id": str(result.inserted_id)}


@router.put("/{id}")
async def update(id: str, data: ContentMappingModel):
    await db.content_mappings.update_one({"_id": ObjectId(id)}, {"$set": data.model_dump(exclude={"id"})})
    return {"updated": True}


@router.delete("/{id}")
async def delete(id: str):
    await db.content_mappings.delete_one({"_id": ObjectId(id)})
    return {"deleted": True}
