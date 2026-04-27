from fastapi import APIRouter, Depends
from app.database import db
from app.auth import decode_token
from datetime import date
import asyncio
import httpx
import os

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
CAT_API = os.getenv("CAT_API_URL", "http://localhost:8001")


@router.get("/training/{training_id}")
async def get_training_detail(training_id: str, user: dict = Depends(decode_token)):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{CAT_API}/trainings/{training_id}")
        if r.status_code != 200:
            from fastapi import HTTPException
            raise HTTPException(404, "Training not found")
        training = r.json()
        ilearn_r = await client.get(f"{CAT_API}/ilearn/courses")
        ilearn_courses_map = {c["cat_course_name"]: c for c in (ilearn_r.json() if ilearn_r.status_code == 200 else []) if c.get("cat_course_name")}

    courses = []
    for group_key in ["basic_groups", "advanced_groups"]:
        for group in training.get(group_key, []):
            for item in group.get("items", []):
                for cname in item.get("courses", []):
                    if cname in ilearn_courses_map:
                        courses.append(ilearn_courses_map[cname])
    return {"training_id": training_id, "training_name": training["name"], "description": training.get("description", ""), "courses": courses}


@router.get("/me")
async def get_my_dashboard(user: dict = Depends(decode_token)):
    user_id = user["sub"]

    # PLEs that are intentionally blocked/pending and not accessible to users
    BLOCKED_EXAMS = {"DSA-ARRAYS-EXPERT PROFICIENCY-PLE"}

    mapping = await db.user_competency_mappings.find_one({"user_id": user_id})
    competency_names = mapping.get("competency_names", ["DSA"]) if mapping else ["DSA"]

    async with httpx.AsyncClient(timeout=10) as client:
        # Fetch all data in parallel
        results = await asyncio.gather(
            client.get(f"{CAT_API}/competency-units/"),
            client.get(f"{CAT_API}/content-mappings/"),
            client.get(f"{CAT_API}/trainings/"),
            client.get(f"{CAT_API}/assessments/"),
            client.get(f"{CAT_API}/competencies/"),
            client.get(f"{CAT_API}/ilearn/courses"),
            client.get(f"{CAT_API}/ilearn/assessments"),
        )

        all_units = results[0].json() if results[0].status_code == 200 else []
        all_mappings = results[1].json() if results[1].status_code == 200 else []
        all_trainings = {t["_id"]: t for t in (results[2].json() if results[2].status_code == 200 else [])}
        all_assessments = {a["_id"]: a for a in (results[3].json() if results[3].status_code == 200 else [])}
        cat_comps = results[4].json() if results[4].status_code == 200 else []
        # Build in-memory lookup maps for iLearn data
        ilearn_courses_map = {c["cat_course_name"]: c for c in (results[5].json() if results[5].status_code == 200 else []) if c.get("cat_course_name")}
        ilearn_assessments_map = {a["cat_exam_name"]: a for a in (results[6].json() if results[6].status_code == 200 else []) if a.get("cat_exam_name")}

        units = [u for u in all_units if u.get("competency") in competency_names]

        progress_doc = await db.user_progress.find_one({"user_id": user_id})
        completed_ids = set(progress_doc.get("completed_course_ids", []) if progress_doc else [])
        completed_assessment_ids = set(progress_doc.get("completed_assessment_ids", []) if progress_doc else [])

        enriched_units = []
        for unit in units:
            unit_name = unit.get("name", "")
            cm = next((m for m in all_mappings if m.get("ce_unit") == unit_name), None)
            ilearn_courses = []
            ilearn_assessments = []

            trainings_grouped = []  # [{training_name, training_id, courses:[]}]
            if cm:
                for tid in (cm.get("training_ids") or []):
                    training = all_trainings.get(tid)
                    if not training:
                        continue
                    t_courses = []
                    for group_key in ["basic_groups", "advanced_groups"]:
                        for group in training.get(group_key, []):
                            for item in group.get("items", []):
                                for cname in item.get("courses", []):
                                    if cname in ilearn_courses_map:
                                        t_courses.append(ilearn_courses_map[cname])
                                        ilearn_courses.append(ilearn_courses_map[cname])
                    trainings_grouped.append({
                        "training_id": tid,
                        "training_name": training["name"],
                        "courses": t_courses,
                    })

                for aid in (cm.get("assessment_ids") or []):
                    assessment = all_assessments.get(aid)
                    if not assessment:
                        continue
                    is_ple = assessment.get("name", "").upper() == "PLE"
                    for group_key in ["expert_groups", "advanced_groups"]:
                        for group in assessment.get(group_key, []):
                            for item in group.get("items", []):
                                for ename in item.get("exams", []):
                                    if ename in ilearn_assessments_map:
                                        entry = dict(ilearn_assessments_map[ename])
                                        if is_ple:
                                            entry["ple_accessible"] = ename not in BLOCKED_EXAMS
                                        ilearn_assessments.append(entry)
                                    else:
                                        # CAT assessment not mapped in iLearn — include as unmapped
                                        ilearn_assessments.append({
                                            "_id": aid,
                                            "cat_exam_name": ename,
                                            "title": ename,
                                            "type": assessment.get("name", "PLE"),
                                            "unmapped": True,
                                            "ple_accessible": False,
                                        })

            all_course_ids = [c["_id"] for c in ilearn_courses]
            all_assessment_ids = [a["_id"] for a in ilearn_assessments]
            courses_done = len(all_course_ids) > 0 and all(cid in completed_ids for cid in all_course_ids)
            assessments_done = len(all_assessment_ids) > 0 and all(aid in completed_assessment_ids for aid in all_assessment_ids)

            # Check release_date on each linked CAT assessment
            today = date.today().isoformat()
            release_info = []  # list of {title, release_date} for locked assessments
            for aid in (cm.get("assessment_ids") or [] if cm else []):
                cat_a = all_assessments.get(aid)
                if cat_a and cat_a.get("release_date"):
                    rd = cat_a["release_date"]
                    if rd > today:
                        release_info.append({"assessment_id": aid, "release_date": rd})

            date_locked = len(release_info) > 0
            assessments_unlocked = not date_locked
            cpa_unlocked = courses_done and not date_locked

            enriched_units.append({
                "unit_id": unit["_id"],
                "unit_name": unit_name,
                "competency": unit.get("competency", ""),
                "plr_table": cm.get("plr_table", "") if cm else "",
                "trainings_grouped": trainings_grouped,
                "ilearn_courses": ilearn_courses,
                "ilearn_assessments": ilearn_assessments,
                "completed_course_ids": list(completed_ids),
                "completed_assessment_ids": list(completed_assessment_ids),
                "assessments_unlocked": assessments_unlocked,
                "cpa_unlocked": cpa_unlocked,
                "release_info": release_info,
                "element_complete": courses_done and assessments_done,
            })

    level_map = {"B": 0, "I": 0, "A": 0, "E": 0}
    for u in enriched_units:
        plr = u.get("plr_table", "").upper()
        if plr in level_map:
            level_map[plr] += 1

    matched_competencies = [c for c in cat_comps if c["name"] in competency_names]
    matched_competencies.sort(key=lambda c: c.get("order", 0))

    # Build chained odyssey — each segment locked until previous is 100%
    odyssey = []
    prev_complete = True
    for comp in matched_competencies:
        comp_units = [u for u in enriched_units if u["competency"] == comp["name"]]
        total = len(comp_units)
        done = sum(1 for u in comp_units if u["element_complete"])
        pct = round((done / total) * 100) if total else 0
        is_complete = pct == 100
        odyssey.append({
            "competency": comp["name"],
            "promotion_from": comp.get("promotion_from") or "",
            "promotion_to": comp.get("promotion_to") or "",
            "elements_done": done,
            "elements_total": total,
            "progress_pct": pct,
            "is_complete": is_complete,
            "locked": not prev_complete,
        })
        prev_complete = is_complete

    current_position = progress_doc.get("current_position", "") if progress_doc else ""
    # Default current_position to first competency's promotion_from if not yet set
    if not current_position and odyssey and odyssey[0]["promotion_from"]:
        current_position = odyssey[0]["promotion_from"]

    return {
        "user": {
            "name": user["name"],
            "email": user["email"],
            "job_title": user.get("job_title", ""),
            "current_position": current_position,
        },
        "competencies": matched_competencies,
        "units": enriched_units,
        "total_elements": len(enriched_units),
        "level_counts": level_map,
        "odyssey": odyssey,
        "current_position": current_position,
    }
