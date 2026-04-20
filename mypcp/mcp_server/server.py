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
async def get_my_competency_elements(user_id: str) -> dict:
    """Get all competency elements assigned to the user across all their competencies.
    Returns a flat numbered list of element names for the user to pick from."""
    names = await _get_competency_names(user_id)
    all_units = await _cat_get("/competency-units/")
    elements = [u["name"] for u in all_units if u.get("competency") in names]
    return {"elements": elements, "count": len(elements)}


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
async def check_assessment_access(user_id: str, competency_element: str, assessment_type: str) -> dict:
    """Check whether the assessment for a specific competency element is accessible.
    Checks release_date lock for all types. Checks training completion only for CPA.
    competency_element = e.g. 'Arrays', assessment_type = e.g. 'CPA', 'PLE', 'CTI'."""
    from datetime import date as _date
    today = _date.today().isoformat()

    all_mappings, all_assessments_list, all_trainings_list, ilearn_courses_list = await _cat_get_many(
        "/content-mappings/", "/assessments/", "/trainings/", "/ilearn/courses"
    )
    all_assessments = {a["_id"]: a for a in all_assessments_list}
    all_trainings = {t["_id"]: t for t in all_trainings_list}
    ilearn_map = {c["cat_course_name"]: c for c in ilearn_courses_list if c.get("cat_course_name")}

    elem_q = competency_element.strip().lower()
    cm = next((m for m in all_mappings if elem_q in m.get("ce_unit", "").lower()), None)
    if not cm:
        return {"found": False, "date_locked": False, "courses_incomplete": False, "release_date": None}

    # Check release_date lock
    locked_dates = [
        cat_a["release_date"]
        for aid in cm.get("assessment_ids", [])
        if (cat_a := all_assessments.get(aid))
        and cat_a.get("release_date")
        and cat_a["release_date"] > today
    ]
    date_locked = len(locked_dates) > 0

    # Training completion check — only applies to CPA
    courses_incomplete = False
    completed_count = 0
    required_course_ids = []
    if assessment_type.upper() == "CPA":
        progress = await db.user_progress.find_one({"user_id": user_id})
        completed_ids = set(progress.get("completed_course_ids", []) if progress else [])
        for tid in cm.get("training_ids", []):
            training = all_trainings.get(tid)
            if not training:
                continue
            for gk in ["basic_groups", "advanced_groups"]:
                for group in training.get(gk, []):
                    for item in group.get("items", []):
                        for cname in item.get("courses", []):
                            if cname in ilearn_map:
                                required_course_ids.append(ilearn_map[cname]["_id"])
        courses_incomplete = len(required_course_ids) > 0 and not all(cid in completed_ids for cid in required_course_ids)
        completed_count = sum(1 for cid in required_course_ids if cid in completed_ids)

    return {
        "found": True,
        "unit": cm.get("ce_unit"),
        "assessment_type": assessment_type.upper(),
        "date_locked": date_locked,
        "release_date": min(locked_dates) if locked_dates else None,
        "courses_incomplete": courses_incomplete,
        "completed_courses": completed_count,
        "total_courses": len(required_course_ids),
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
async def get_trainings_for_element(user_id: str, competency_element: str) -> dict:
    """Get all training names mapped to a specific competency element (ce_unit) for the user.
    Returns a list of training names the user can pick from."""
    all_mappings, all_trainings_list = await _cat_get_many("/content-mappings/", "/trainings/")
    elem_q = competency_element.strip().lower()
    cm = next((m for m in all_mappings if elem_q in m.get("ce_unit", "").lower()), None)
    if not cm:
        return {"found": False, "trainings": []}
    all_trainings = {t["_id"]: t["name"] for t in all_trainings_list}
    training_names = [all_trainings[tid] for tid in cm.get("training_ids", []) if tid in all_trainings]
    return {"found": True, "competency_element": cm.get("ce_unit"), "trainings": training_names}


@mcp.tool
async def check_training_has_courses(training_name: str) -> dict:
    """Check if a specific training has any iLearn courses mapped to it.
    Returns has_courses=True with course names, or has_courses=False if nothing is mapped."""
    all_trainings_list, ilearn_courses_list = await _cat_get_many("/trainings/", "/ilearn/courses")
    training_q = training_name.strip().lower()
    training = next((t for t in all_trainings_list if training_q in t["name"].lower()), None)
    if not training:
        return {"found": False, "has_courses": False, "courses": []}
    ilearn_names = {c["cat_course_name"] for c in ilearn_courses_list if c.get("cat_course_name")}
    courses = []
    for group_key in ["basic_groups", "advanced_groups"]:
        for group in training.get(group_key, []):
            for item in group.get("items", []):
                for cname in item.get("courses", []):
                    if cname in ilearn_names:
                        courses.append(cname)
    return {"found": True, "training_name": training["name"], "has_courses": len(courses) > 0, "courses": courses}


@mcp.tool
async def check_ple_mapped(user_id: str, competency_element: str) -> dict:
    """Check if a PLE assessment is mapped and accessible in iLearn for a specific competency element.
    Returns a list of all PLE exam names under that element with mapped_in_ilearn and accessible flags."""
    all_mappings, all_assessments_list, ilearn_assessments_list = await _cat_get_many(
        "/content-mappings/", "/assessments/", "/ilearn/assessments"
    )
    all_assessments = {a["_id"]: a for a in all_assessments_list}
    ilearn_exam_names = {a["cat_exam_name"] for a in ilearn_assessments_list if a.get("cat_exam_name")}

    # PLEs that are intentionally blocked/pending and not accessible to users
    BLOCKED_EXAMS = {"DSA-ARRAYS-EXPERT PROFICIENCY-PLE"}

    elem_q = competency_element.strip().lower()
    cm = next((m for m in all_mappings if elem_q in m.get("ce_unit", "").lower()), None)
    if not cm:
        return {"found": False, "competency_element": competency_element, "ple_exams": []}

    ple_exams = []
    for aid in cm.get("assessment_ids", []):
        cat_a = all_assessments.get(aid)
        if not cat_a or cat_a.get("name", "").upper() != "PLE":
            continue
        for gk in ["expert_groups", "advanced_groups"]:
            for group in cat_a.get(gk, []):
                for item in group.get("items", []):
                    for ename in item.get("exams", []):
                        mapped = ename in ilearn_exam_names
                        accessible = mapped and ename not in BLOCKED_EXAMS
                        ple_exams.append({
                            "exam_name": ename,
                            "mapped_in_ilearn": mapped,
                            "accessible": accessible,
                        })

    if not ple_exams:
        return {"found": True, "competency_element": cm.get("ce_unit"), "ple_exams": []}

    return {"found": True, "competency_element": cm.get("ce_unit"), "ple_exams": ple_exams}


@mcp.tool
async def check_my_odyssey_config(user_id: str) -> dict:
    """Check odyssey (promotion tier) configuration for all competencies assigned to the user.
    Returns which competencies are configured and which are not."""
    names = await _get_competency_names(user_id)
    all_comps = await _cat_get("/competencies/")
    result = []
    for name in names:
        comp = next((c for c in all_comps if c["name"] == name), None)
        if not comp:
            result.append({"competency": name, "configured": False, "promotion_from": "", "promotion_to": ""})
        else:
            has_from = bool(comp.get("promotion_from"))
            has_to = bool(comp.get("promotion_to"))
            result.append({
                "competency": comp["name"],
                "configured": has_from and has_to,
                "promotion_from": comp.get("promotion_from") or "",
                "promotion_to": comp.get("promotion_to") or "",
            })
    not_configured = [r for r in result if not r["configured"]]
    not_configured_names = [r["competency"] for r in not_configured]
    # Build the display message so the LLM just shows it as-is
    if not_configured_names:
        names_str = ", ".join(f"'{n}'" for n in not_configured_names)
        display_message = f"Your Odyssey for the competency {names_str} is not configured. Please contact your PSD Manager/manager to create your FSP (Fixed Step Promotion) profile. They can assist you on this request, as they create it which depends on your role, profile and requirements needed."
    else:
        display_message = "Your Odyssey is configured for all your competencies."
    return {
        "display_message": display_message,
        "all_configured": len(not_configured) == 0,
        "not_configured": not_configured_names,
        "competencies": result,
    }


@mcp.tool
async def get_my_trainings(user_id: str) -> dict:
    """Get all trainings assigned to the user with their mapped courses, grouped by competency element."""
    names = await _get_competency_names(user_id)
    all_units, all_mappings, all_trainings_list, ilearn_courses_list = await _cat_get_many(
        "/competency-units/", "/content-mappings/", "/trainings/", "/ilearn/courses"
    )
    units = [u for u in all_units if u.get("competency") in names]
    all_trainings = {t["_id"]: t for t in all_trainings_list}
    ilearn_map = {c["cat_course_name"]: c["title"] for c in ilearn_courses_list if c.get("cat_course_name")}

    result = []
    for unit in units:
        cm = next((m for m in all_mappings if m.get("ce_unit") == unit["name"]), None)
        if not cm:
            continue
        trainings = []
        for tid in cm.get("training_ids", []):
            t = all_trainings.get(tid)
            if not t:
                continue
            courses = [
                ilearn_map[cname]
                for gk in ["basic_groups", "advanced_groups"]
                for g in t.get(gk, [])
                for item in g.get("items", [])
                for cname in item.get("courses", [])
                if cname in ilearn_map
            ]
            trainings.append({"training_name": t["name"], "courses": courses, "course_count": len(courses)})
        result.append({
            "competency": unit.get("competency"),
            "competency_element": unit["name"],
            "trainings": trainings,
            "training_count": len(trainings),
        })
    return {"total_trainings": sum(r["training_count"] for r in result), "elements": result}


@mcp.tool
async def get_element_requirements(user_id: str, competency_element: str) -> dict:
    """Get all requirements for a specific competency element: PLR level, assessment types, trainings and their courses."""
    all_units, all_mappings, all_trainings_list, ilearn_courses_list = await _cat_get_many(
        "/competency-units/", "/content-mappings/", "/trainings/", "/ilearn/courses"
    )
    elem_q = competency_element.strip().lower()
    unit = next((u for u in all_units if elem_q in u["name"].lower()), None)
    if not unit:
        return {"found": False, "competency_element": competency_element}
    cm = next((m for m in all_mappings if m.get("ce_unit") == unit["name"]), None)
    if not cm:
        return {"found": True, "competency_element": unit["name"], "plr_level": "", "assessment_types": [], "trainings": []}
    all_trainings = {t["_id"]: t for t in all_trainings_list}
    ilearn_map = {c["cat_course_name"]: c["title"] for c in ilearn_courses_list if c.get("cat_course_name")}
    trainings = []
    for tid in cm.get("training_ids", []):
        t = all_trainings.get(tid)
        if not t:
            continue
        courses = [
            ilearn_map[cname]
            for gk in ["basic_groups", "advanced_groups"]
            for g in t.get(gk, [])
            for item in g.get("items", [])
            for cname in item.get("courses", [])
            if cname in ilearn_map
        ]
        trainings.append({"training_name": t["name"], "courses": courses})
    return {
        "found": True,
        "competency_element": unit["name"],
        "competency": unit.get("competency", ""),
        "plr_level": cm.get("plr_table", ""),
        "assessment_types": cm.get("assessment_types", []),
        "trainings": trainings,
        "total_courses": sum(len(t["courses"]) for t in trainings),
    }


@mcp.tool
async def get_my_progress_summary(user_id: str) -> dict:
    """Get a summary of the user's progress: how many courses and assessments completed vs total."""
    progress = await db.user_progress.find_one({"user_id": user_id})
    completed_courses = len(progress.get("completed_course_ids", [])) if progress else 0
    completed_assessments = len(progress.get("completed_assessment_ids", [])) if progress else 0
    courses_data = await _get_my_courses_data(user_id)
    total_courses = courses_data["count"]
    return {
        "completed_courses": completed_courses,
        "total_courses": total_courses,
        "completed_assessments": completed_assessments,
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
