from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.auth import decode_token
from app.database import db

router = APIRouter(prefix="/certifications", tags=["Certifications"])

CERT_TYPES = {"ilearn", "xylem", "cbt"}


def _safe_date(value: str | None) -> str:
    if not value:
        return "N/A"
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d-%b-%Y")
    except Exception:
        return value


def _status_chip(raw_status: str | None) -> str:
    status = (raw_status or "").strip().lower()
    if status in {"valid", "expired", "pending"}:
        return status
    return "pending"


@router.get("/me")
async def get_my_certifications(user: dict = Depends(decode_token)):
    user_id = user["sub"]
    rows = await db.certifications.find({"user_id": user_id}).to_list(500)

    cards = ["generic", "function", "local", "learning"]
    counts = {
        "summary": {"done": 0, "total": 0, "pct": 0},
        **{k: {"done": 0, "total": 0, "pct": 0} for k in cards},
    }

    certs = []
    for row in rows:
        ctype = (row.get("certification_type") or "").strip().lower()
        if ctype not in CERT_TYPES:
            continue

        status = _status_chip(row.get("validity_status"))
        category = (row.get("certification_category") or "").strip().lower()

        counts["summary"]["total"] += 1
        if status == "valid":
            counts["summary"]["done"] += 1

        if category in counts:
            counts[category]["total"] += 1
            if status == "valid":
                counts[category]["done"] += 1

        certs.append(
            {
                "id": str(row.get("_id")),
                "name": row.get("certification_name", "Untitled"),
                "certification_type": ctype,
                "certification_category": category,
                "validity_status": status,
                "expires_on": _safe_date(row.get("expires_on")),
                "provider": row.get("provider", "N/A"),
                "description": row.get("description", ""),
                "ticket_queue": "GBS-HSE-MYPCP-L1",
            }
        )

    for key, value in counts.items():
        value["pct"] = round((value["done"] / value["total"]) * 100) if value["total"] else 0

    certs.sort(key=lambda c: (c["validity_status"] != "expired", c["name"].lower()))

    return {
        "user": {
            "name": user.get("name", "User"),
            "email": user.get("email", ""),
            "job_title": user.get("job_title", "Contractor"),
        },
        "summary": counts,
        "total_certifications": counts["summary"]["total"],
        "overall_training_coefficient": counts["summary"]["pct"],
        "certifications": certs,
    }


@router.get("/{certification_id}")
async def get_certification_detail(certification_id: str, user: dict = Depends(decode_token)):
    user_id = user["sub"]
    if not ObjectId.is_valid(certification_id):
        raise HTTPException(status_code=404, detail="Certification not found")

    cert = await db.certifications.find_one({"_id": ObjectId(certification_id), "user_id": user_id})
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")

    ctype = (cert.get("certification_type") or "").strip().lower()
    status = _status_chip(cert.get("validity_status"))

    return {
        "id": str(cert.get("_id")),
        "name": cert.get("certification_name", "Untitled"),
        "certification_type": ctype,
        "certification_category": (cert.get("certification_category") or "").strip().lower(),
        "validity_status": status,
        "expires_on": _safe_date(cert.get("expires_on")),
        "provider": cert.get("provider", "N/A"),
        "description": cert.get("description", ""),
        "evidence_link": cert.get("evidence_link", ""),
    }