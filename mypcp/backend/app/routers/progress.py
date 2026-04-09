from fastapi import APIRouter, Depends
from app.database import db
from app.auth import decode_token
import httpx, os

router = APIRouter(prefix="/progress", tags=["Progress"])
CAT_API = os.getenv("CAT_API_URL", "http://localhost:8001")


async def _check_and_update_position(user_id: str):
    """After any completion, check if a competency is 100% done and update current_position."""
    mapping = await db.user_competency_mappings.find_one({"user_id": user_id})
    competency_names = mapping.get("competency_names", []) if mapping else []
    if not competency_names:
        return

    progress_doc = await db.user_progress.find_one({"user_id": user_id})
    completed_courses = set(progress_doc.get("completed_course_ids", []) if progress_doc else [])
    completed_assessments = set(progress_doc.get("completed_assessment_ids", []) if progress_doc else [])

    async with httpx.AsyncClient(timeout=10) as client:
        r_units = await client.get(f"{CAT_API}/competency-units/")
        r_mappings = await client.get(f"{CAT_API}/content-mappings/")
        r_trainings = await client.get(f"{CAT_API}/trainings/")
        r_assessments = await client.get(f"{CAT_API}/assessments/")
        r_comps = await client.get(f"{CAT_API}/competencies/")
        r_ilearn_c = await client.get(f"{CAT_API}/ilearn/courses")
        r_ilearn_a = await client.get(f"{CAT_API}/ilearn/assessments")

    all_units = r_units.json() if r_units.status_code == 200 else []
    all_mappings = r_mappings.json() if r_mappings.status_code == 200 else []
    all_trainings = {t["_id"]: t for t in (r_trainings.json() if r_trainings.status_code == 200 else [])}
    all_assessments = {a["_id"]: a for a in (r_assessments.json() if r_assessments.status_code == 200 else [])}
    cat_comps = sorted(
        [c for c in (r_comps.json() if r_comps.status_code == 200 else []) if c["name"] in competency_names],
        key=lambda c: c.get("order", 0)
    )
    ilearn_courses_map = {c["cat_course_name"]: c for c in (r_ilearn_c.json() if r_ilearn_c.status_code == 200 else []) if c.get("cat_course_name")}
    ilearn_assessments_map = {a["cat_exam_name"]: a for a in (r_ilearn_a.json() if r_ilearn_a.status_code == 200 else []) if a.get("cat_exam_name")}

    new_position = None
    for comp in cat_comps:
        comp_units = [u for u in all_units if u.get("competency") == comp["name"]]
        all_done = True
        for unit in comp_units:
            cm = next((m for m in all_mappings if m.get("ce_unit") == unit["name"]), None)
            if not cm:
                all_done = False; break
            course_ids = [
                ilearn_courses_map[cname]["_id"]
                for tid in cm.get("training_ids", [])
                if (t := all_trainings.get(tid))
                for gk in ["basic_groups", "advanced_groups"]
                for g in t.get(gk, [])
                for item in g.get("items", [])
                for cname in item.get("courses", [])
                if cname in ilearn_courses_map
            ]
            assessment_ids = [
                ilearn_assessments_map[ename]["_id"]
                for aid in cm.get("assessment_ids", [])
                if (a := all_assessments.get(aid))
                for gk in ["expert_groups", "advanced_groups"]
                for g in a.get(gk, [])
                for item in g.get("items", [])
                for ename in item.get("exams", [])
                if ename in ilearn_assessments_map
            ]
            if not (course_ids and all(cid in completed_courses for cid in course_ids) and
                    assessment_ids and all(aid in completed_assessments for aid in assessment_ids)):
                all_done = False; break
        if all_done and comp.get("promotion_to"):
            new_position = comp["promotion_to"]

    if new_position:
        await db.user_progress.update_one(
            {"user_id": user_id},
            {"$set": {"current_position": new_position}},
            upsert=True
        )


@router.post("/course/{course_id}/complete")
async def toggle_course_complete(course_id: str, user: dict = Depends(decode_token)):
    user_id = user["sub"]
    doc = await db.user_progress.find_one({"user_id": user_id})
    completed = set(doc.get("completed_course_ids", [])) if doc else set()

    if course_id in completed:
        completed.discard(course_id)
    else:
        completed.add(course_id)

    await db.user_progress.update_one(
        {"user_id": user_id},
        {"$set": {"completed_course_ids": list(completed)}},
        upsert=True,
    )
    await _check_and_update_position(user_id)
    return {"completed_course_ids": list(completed)}


@router.post("/assessment/{assessment_id}/complete")
async def toggle_assessment_complete(assessment_id: str, user: dict = Depends(decode_token)):
    user_id = user["sub"]
    doc = await db.user_progress.find_one({"user_id": user_id})
    completed = set(doc.get("completed_assessment_ids", [])) if doc else set()

    if assessment_id in completed:
        completed.discard(assessment_id)
    else:
        completed.add(assessment_id)

    await db.user_progress.update_one(
        {"user_id": user_id},
        {"$set": {"completed_assessment_ids": list(completed)}},
        upsert=True,
    )
    await _check_and_update_position(user_id)
    return {"completed_assessment_ids": list(completed)}


@router.get("/me")
async def get_my_progress(user: dict = Depends(decode_token)):
    doc = await db.user_progress.find_one({"user_id": user["sub"]})
    return {"completed_course_ids": doc.get("completed_course_ids", []) if doc else []}
