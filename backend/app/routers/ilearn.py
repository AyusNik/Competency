from fastapi import APIRouter, Query, HTTPException
from app.database import ilearn_db, db as cat_db
from bson import ObjectId
from typing import Optional

router = APIRouter(prefix="/ilearn", tags=["ILearn"])


def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc


# ── Courses (ilearn_db) ──────────────────────────────────────

@router.get("/courses")
async def get_courses(search: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    filters = []
    if search:
        filters.append({"$or": [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}},
        ]})
    if category and category != "All":
        filters.append({"category": category})
    query = {"$and": filters} if filters else {}
    return [serialize(c) async for c in ilearn_db.courses.find(query)]


@router.get("/courses/{id}")
async def get_course(id: str):
    doc = await ilearn_db.courses.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(404, "Course not found")
    result = serialize(doc)
    # Cross-reference: find CAT trainings that reference this course by cat_course_name
    cat_name = doc.get("cat_course_name", "")
    mapped_trainings = []
    async for t in cat_db.trainings.find():
        for group_key in ["basic_groups", "advanced_groups"]:
            for group in t.get(group_key, []):
                for item in group.get("items", []):
                    if cat_name in item.get("courses", []):
                        mapped_trainings.append({
                            "training_id": str(t["_id"]),
                            "training_name": t["name"],
                            "group": group["group_name"],
                            "tab": group_key.replace("_groups", ""),
                        })
    result["mapped_trainings"] = mapped_trainings
    return result


@router.post("/courses", status_code=201)
async def create_course(data: dict):
    result = await ilearn_db.courses.insert_one(data)
    return {"id": str(result.inserted_id)}


@router.put("/courses/{id}")
async def update_course(id: str, data: dict):
    await ilearn_db.courses.update_one({"_id": ObjectId(id)}, {"$set": data})
    return {"updated": True}


@router.delete("/courses/{id}")
async def delete_course(id: str):
    await ilearn_db.courses.delete_one({"_id": ObjectId(id)})
    return {"deleted": True}


# ── Assessments (ilearn_db) ──────────────────────────────────

@router.get("/assessments")
async def get_assessments(search: Optional[str] = Query(None), category: Optional[str] = Query(None), type: Optional[str] = Query(None)):
    filters = []
    if search:
        filters.append({"$or": [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]})
    if category and category != "All":
        filters.append({"category": category})
    if type and type != "All":
        filters.append({"type": type})
    query = {"$and": filters} if filters else {}
    return [serialize(a) async for a in ilearn_db.assessments.find(query)]


@router.get("/assessments/{id}")
async def get_assessment(id: str):
    doc = await ilearn_db.assessments.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(404, "Assessment not found")
    result = serialize(doc)
    # Cross-reference: find CAT assessment docs that reference this exam
    cat_exam_name = doc.get("cat_exam_name", "")
    mapped = []
    async for a in cat_db.assessments.find():
        for group_key in ["expert_groups", "advanced_groups"]:
            for group in a.get(group_key, []):
                for item in group.get("items", []):
                    if cat_exam_name in item.get("exams", []):
                        mapped.append({
                            "cat_assessment_id": str(a["_id"]),
                            "type": a["name"],
                            "competency_element": a["competency_element"],
                        })
    result["mapped_cat_assessments"] = mapped
    return result


@router.post("/assessments", status_code=201)
async def create_assessment(data: dict):
    result = await ilearn_db.assessments.insert_one(data)
    return {"id": str(result.inserted_id)}


@router.put("/assessments/{id}")
async def update_assessment(id: str, data: dict):
    await ilearn_db.assessments.update_one({"_id": ObjectId(id)}, {"$set": data})
    return {"updated": True}


@router.delete("/assessments/{id}")
async def delete_assessment(id: str):
    await ilearn_db.assessments.delete_one({"_id": ObjectId(id)})
    return {"deleted": True}


# ── Metadata ─────────────────────────────────────────────────

@router.get("/categories")
async def get_categories():
    cats = await ilearn_db.courses.distinct("category")
    return sorted(set(cats))


@router.get("/stats")
async def get_stats():
    return {
        "total_courses": await ilearn_db.courses.count_documents({}),
        "total_assessments": await ilearn_db.assessments.count_documents({}),
        "categories": await ilearn_db.courses.distinct("category"),
    }


# ── Lookup by CAT name (cross-reference) ─────────────────────

@router.get("/lookup/course")
async def lookup_course(name: str):
    doc = await ilearn_db.courses.find_one({"cat_course_name": name})
    if not doc:
        raise HTTPException(404, f"No ILearn course mapped to '{name}'")
    return serialize(doc)


@router.get("/lookup/assessment")
async def lookup_assessment(name: str):
    doc = await ilearn_db.assessments.find_one({"cat_exam_name": name})
    if not doc:
        raise HTTPException(404, f"No ILearn assessment mapped to '{name}'")
    return serialize(doc)


# ── Lookup by CAT name (for chip open_in_new links) ───────────

@router.get("/lookup/course")
async def lookup_course_by_cat_name(name: str = Query(...)):
    """Given a cat_course_name string, return the matching ILearn course (id + url + title)."""
    doc = await ilearn_db.courses.find_one({"cat_course_name": name})
    if not doc:
        raise HTTPException(404, "No ILearn course mapped to this name")
    return {"_id": str(doc["_id"]), "title": doc["title"], "url": doc["url"], "type": doc["type"]}


@router.get("/lookup/assessment")
async def lookup_assessment_by_cat_name(name: str = Query(...)):
    """Given a cat_exam_name string, return the matching ILearn assessment (id + url + title)."""
    doc = await ilearn_db.assessments.find_one({"cat_exam_name": name})
    if not doc:
        raise HTTPException(404, "No ILearn assessment mapped to this name")
    return {"_id": str(doc["_id"]), "title": doc["title"], "url": doc["url"], "type": doc["type"]}
