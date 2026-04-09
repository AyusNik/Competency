from fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import httpx
import os
import logging

# Suppress Windows asyncio pipe transport noise
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

load_dotenv()

mcp = FastMCP("MyPCP MCP Server")

_client = AsyncIOMotorClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = _client[os.getenv("DB_NAME", "mypcp_db")]
CAT_API = os.getenv("CAT_API_URL", "http://localhost:8005")

_http = httpx.AsyncClient(timeout=10, base_url=CAT_API)


# ── Helpers ───────────────────────────────────────────────────

async def _cat_get(path: str) -> list:
    r = await _http.get(path)
    return r.json() if r.status_code == 200 else []


async def _cat_get_many(*paths: str) -> list:
    results = await asyncio.gather(*[_cat_get(p) for p in paths])
    return list(results)


async def _get_competency_names(user_id: str) -> list[str]:
    mapping = await db.user_competency_mappings.find_one({"user_id": user_id})
    return mapping.get("competency_names", ["DSA"]) if mapping else ["DSA"]


# ── Tools ─────────────────────────────────────────────────────

@mcp.tool
async def get_user_profile(user_id: str) -> dict:
    """Get the profile of a MyPCP user (name, job title, email)."""
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return {"error": "User not found"}
    return {"name": user["name"], "email": user["email"], "job_title": user.get("job_title", "")}


@mcp.tool
async def get_my_competencies(user_id: str) -> dict:
    """Get all competencies assigned to a user."""
    names = await _get_competency_names(user_id)
    all_comps = await _cat_get("/competencies/")
    matched = [c for c in all_comps if c["name"] in names]
    return {"competencies": matched, "count": len(matched)}


async def _get_my_courses_data(user_id: str) -> dict:
    """Internal helper — same logic as get_my_courses but callable directly."""
    names = await _get_competency_names(user_id)
    all_units, all_mappings, all_trainings_list, ilearn_courses_list = await _cat_get_many(
        "/competency-units/", "/content-mappings/", "/trainings/", "/ilearn/courses"
    )
    units = [u for u in all_units if u.get("competency") in names]
    all_trainings = {t["_id"]: t for t in all_trainings_list}
    ilearn_map = {c["cat_course_name"]: c for c in ilearn_courses_list if c.get("cat_course_name")}

    courses = []
    seen = set()
    for unit in units:
        cm = next((m for m in all_mappings if m.get("ce_unit") == unit["name"]), None)
        if not cm:
            continue
        for tid in cm.get("training_ids", []):
            training = all_trainings.get(tid)
            if not training:
                continue
            for gk in ["basic_groups", "advanced_groups"]:
                for group in training.get(gk, []):
                    for item in group.get("items", []):
                        for cname in item.get("courses", []):
                            if cname in seen or cname not in ilearn_map:
                                continue
                            seen.add(cname)
                            course = dict(ilearn_map[cname])
                            course["unit"] = unit["name"]
                            courses.append(course)
    return {"courses": courses, "count": len(courses)}


@mcp.tool
async def get_my_courses(user_id: str) -> dict:
    """Get all iLearn courses assigned to a user via their competency mappings."""
    return await _get_my_courses_data(user_id)


@mcp.tool
async def get_my_assessments(user_id: str) -> dict:
    """Get all iLearn assessments assigned to a user via their competency mappings."""
    names = await _get_competency_names(user_id)
    all_units, all_mappings, all_assessments_list, ilearn_assessments_list = await _cat_get_many(
        "/competency-units/", "/content-mappings/", "/assessments/", "/ilearn/assessments"
    )
    units = [u for u in all_units if u.get("competency") in names]
    all_assessments = {a["_id"]: a for a in all_assessments_list}
    ilearn_map = {a["cat_exam_name"]: a for a in ilearn_assessments_list if a.get("cat_exam_name")}

    assessments = []
    seen = set()
    for unit in units:
        cm = next((m for m in all_mappings if m.get("ce_unit") == unit["name"]), None)
        if not cm:
            continue
        for aid in cm.get("assessment_ids", []):
            assessment = all_assessments.get(aid)
            if not assessment:
                continue
            for gk in ["expert_groups", "advanced_groups"]:
                for group in assessment.get(gk, []):
                    for item in group.get("items", []):
                        for ename in item.get("exams", []):
                            if ename in seen or ename not in ilearn_map:
                                continue
                            seen.add(ename)
                            a = dict(ilearn_map[ename])
                            a["unit"] = unit["name"]
                            assessments.append(a)
    return {"assessments": assessments, "count": len(assessments)}


@mcp.tool
async def check_course_assigned(user_id: str, course_title: str) -> dict:
    """Check if a specific course (by partial title) is assigned to the user and whether it is available."""
    result = await _get_my_courses_data(user_id)
    query = course_title.lower()
    matched = [c for c in result.get("courses", []) if query in c.get("title", "").lower()]
    if not matched:
        return {"assigned": False, "available": True, "matched_courses": []}
    unavailable = any(c.get("available") is False for c in matched)
    return {"assigned": True, "available": not unavailable, "matched_courses": matched}


@mcp.tool
async def raise_ticket(user_id: str, course_title: str, issue: str) -> dict:
    """Raise a support ticket for a user regarding a course content issue."""
    ticket = {
        "user_id": user_id,
        "course_title": course_title,
        "issue": issue,
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
    }
    result = await db.tickets.insert_one(ticket)
    ticket_id = str(result.inserted_id)
    return {"ticket_id": ticket_id, "status": "open", "message": f"Ticket #{ticket_id[:8]} raised successfully for '{course_title}'."}


@mcp.tool
async def validate_competency_unit(user_id: str, competency_unit: str) -> dict:
    """Validate that a competency unit name exists in the user's assigned competencies.
    Returns valid=True with the exact matched name, or valid=False with a list of available unit names."""
    names = await _get_competency_names(user_id)
    query = competency_unit.strip().lower()
    matched = next((n for n in names if query in n.lower()), None)
    if matched:
        return {"valid": True, "matched_name": matched}
    return {"valid": False, "matched_name": None, "available_units": names}


@mcp.tool
async def validate_competency_element(user_id: str, competency_unit: str, competency_element: str) -> dict:
    """Validate that a competency element exists under the given competency unit.
    Returns valid=True with the exact matched name, or valid=False with available element names."""
    all_units = await _cat_get("/competency-units/")
    unit_q = competency_unit.strip().lower()
    elem_q = competency_element.strip().lower()
    # competency-units have a 'competency' field matching the competency name
    elements_in_unit = [u for u in all_units if unit_q in u.get("competency", "").lower()]
    if not elements_in_unit:
        return {"valid": False, "matched_name": None, "available_elements": []}
    matched = next((u for u in elements_in_unit if elem_q in u["name"].lower()), None)
    if matched:
        return {"valid": True, "matched_name": matched["name"]}
    return {"valid": False, "matched_name": None, "available_elements": [u["name"] for u in elements_in_unit]}


@mcp.tool
async def check_assessment_access(user_id: str, competency_unit: str, competency_element: str) -> dict:
    """Check whether the assessment for a specific competency element has a release_date blocking access.
    competency_unit = e.g. 'DSA', competency_element = e.g. 'Arrays' (the competency-unit record name)."""
    from datetime import date as _date
    today = _date.today().isoformat()

    all_mappings, all_assessments_list = await _cat_get_many("/content-mappings/", "/assessments/")
    all_assessments = {a["_id"]: a for a in all_assessments_list}

    # ce_unit in content-mappings stores the competency-unit name (e.g. "Arrays")
    elem_q = competency_element.strip().lower()
    cm = next((m for m in all_mappings if elem_q in m.get("ce_unit", "").lower()), None)
    if not cm:
        return {"found": False, "date_locked": False, "release_date": None}

    locked_dates = [
        cat_a["release_date"]
        for aid in cm.get("assessment_ids", [])
        if (cat_a := all_assessments.get(aid))
        and cat_a.get("release_date")
        and cat_a["release_date"] > today
    ]
    return {
        "found": True,
        "unit": cm.get("ce_unit"),
        "date_locked": len(locked_dates) > 0,
        "release_date": min(locked_dates) if locked_dates else None,
    }


@mcp.tool
async def check_odyssey_config(competency_name: str) -> dict:
    """Check if a competency has promotion_from and promotion_to configured.
    Returns configured=True with the values, or configured=False if missing."""
    all_comps = await _cat_get("/competencies/")
    query = competency_name.strip().lower()
    comp = next((c for c in all_comps if query in c["name"].lower()), None)
    if not comp:
        return {"found": False, "configured": False, "competency_name": competency_name}
    has_from = bool(comp.get("promotion_from"))
    has_to = bool(comp.get("promotion_to"))
    return {
        "found": True,
        "competency_name": comp["name"],
        "configured": has_from and has_to,
        "promotion_from": comp.get("promotion_from") or "",
        "promotion_to": comp.get("promotion_to") or "",
    }


@mcp.tool
async def get_manager_details(user_id: str) -> dict:
    """Get the Business Line Manager contact details for a user."""
    mgr = await db.user_managers.find_one({"user_id": user_id})
    if not mgr:
        return {"error": "No manager assigned to this user"}
    return {
        "manager_name": mgr.get("manager_name"),
        "manager_email": mgr.get("manager_email"),
        "manager_phone": mgr.get("manager_phone"),
        "manager_title": mgr.get("manager_title"),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8003, path="/mcp")
