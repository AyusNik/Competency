from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import db
from app.auth import decode_token
from app.agent import get_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from datetime import datetime
import re

import json

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


STOPWORDS = {
    "i", "want", "to", "get", "be", "this", "that", "my", "me", "with", "for", "the",
    "a", "an", "please", "certificate", "certification", "course", "assigned", "assign", "unassign",
    "validate", "validation", "particular", "of", "in",
}


CERT_INTENTS = {"assign", "unassign", "validate"}


def _extract_context_sentence(new_messages: list) -> str:
    """Extract the display_message or build the context sentence from tool results."""
    training_name = ""
    element_name = ""
    ple_exam_name = ""
    ple_inaccessible = False

    for m in new_messages:
        if not isinstance(m, ToolMessage):
            continue
        try:
            data = json.loads(m.content)
        except Exception:
            continue

        # Odyssey tool
        if "display_message" in data and "not_configured" in data:
            if not data.get("all_configured"):
                return data["display_message"]

        # Assessment access tool — only prepend if actually locked
        if "date_locked" in data and "unit" in data:
            if data.get("date_locked"):
                unit = data.get("unit", "")
                return f"The assessment for **'{unit}'** is currently locked. To resolve this issue, please connect with your Business Line Manager:"

        # Training has no courses
        if "has_courses" in data and "training_name" in data:
            if not data.get("has_courses"):
                training_name = data.get("training_name", "this training")

        # PLE mapped check — capture inaccessible PLE
        if "ple_exams" in data:
            element_name = data.get("competency_element", element_name)
            for exam in data.get("ple_exams", []):
                if not exam.get("accessible", True):
                    ple_exam_name = exam.get("exam_name", "")
                    ple_inaccessible = True

        # Validate element — capture matched element name
        if "matched_name" in data and data.get("valid") and "available_elements" not in data:
            element_name = data.get("matched_name", "")

    # PLE inaccessible
    if ple_inaccessible and ple_exam_name:
        parts = [f"The PLE **'{ple_exam_name}'**"]
        if element_name:
            parts.append(f"under **'{element_name}'**")
        parts.append("is not working in iLearn. To resolve this issue, please connect with your Business Line Manager:")
        return " ".join(parts)

    # Build no-courses sentence if training has no courses
    if training_name:
        parts = [f"No courses are mapped under the training **'{training_name}'**"]
        if element_name:
            parts.append(f"for the competency element **'{element_name}'**")
        parts.append(". To resolve this issue, please connect with your Business Line Manager:")
        return " ".join(parts)

    return ""


def _ensure_context_prefix(ai_reply: str, new_messages: list) -> str:
    """If the reply starts directly with manager details, prepend the context sentence."""
    manager_starters = [
        "**your business line manager",
        "here are your business line",
        "**name:**",
        "- **name:**",
        "👤",
        "your business line manager",
    ]
    reply_lower = ai_reply.strip().lower()
    starts_with_manager = any(reply_lower.startswith(s) for s in manager_starters)
    if starts_with_manager:
        context = _extract_context_sentence(new_messages)
        if context:
            return context + "\n\n" + ai_reply
    return ai_reply


def _serialize_messages(messages: list) -> list:
    """Serialize all message types to JSON-safe dicts."""
    result = []
    for m in messages:
        if isinstance(m, HumanMessage):
            result.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            entry = {"role": "assistant", "content": m.content or ""}
            if m.tool_calls:
                entry["tool_calls"] = m.tool_calls
            result.append(entry)
        elif isinstance(m, ToolMessage):
            result.append({
                "role": "tool",
                "content": m.content,
                "tool_call_id": m.tool_call_id,
            })
    return result


def _deserialize_messages(raw: list) -> list:
    """Deserialize stored dicts back to LangChain message objects."""
    messages = []
    for m in raw:
        role = m.get("role")
        if role == "user":
            messages.append(HumanMessage(content=m["content"]))
        elif role == "assistant":
            tool_calls = m.get("tool_calls")
            if tool_calls:
                messages.append(AIMessage(content=m.get("content", ""), tool_calls=tool_calls))
            else:
                messages.append(AIMessage(content=m["content"]))
        elif role == "tool":
            messages.append(ToolMessage(content=m["content"], tool_call_id=m["tool_call_id"]))
    return messages


UNASSIGN_CERT_REPLY = """Hello ,
Please follow the steps below to unassign the certification.

Please be informed that this issue needs a new ticket to the GBS team.
Portal: https://esm.slb.com
Create the ticket from esm.slb.com using queue: GBS-HSE-MYPCP-L1.

The team will review your request and process the unassignment.

STEP 1
[[CERT_STEP_1]]

STEP 2
[[CERT_STEP_2]]"""


ASSIGN_CERT_REPLY = """Hello ,
Please follow the steps below to assign the certification.

Please be informed that this issue needs a new ticket to the GBS team.
Portal: https://esm.slb.com
Create the ticket from esm.slb.com using queue: GBS-HSE-MYPCP-L1.

The team will review your request and process the assignment.

STEP 1
[[CERT_STEP_1]]

STEP 2
[[CERT_STEP_2]]"""


VALIDATE_CBT_REPLY = """Hello ,
Please follow the steps below to validate the Classroom Based Certification (CBT).

Please be informed that this issue needs a new ticket to the GBS team.
Portal: https://esm.slb.com
Create the ticket from esm.slb.com using queue: GBS-HSE-MYPCP-L1.

The team will review your request and process the validation.

STEP 1
[[CERT_STEP_1]]

STEP 2
[[CERT_STEP_2]]"""


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def _tokenize(text: str) -> set[str]:
    return {t for t in _normalize_text(text).split() if t and t not in STOPWORDS}


def _best_matching_certificate(message: str, certs: list[dict]) -> dict | None:
    normalized_message = _normalize_text(message)

    for cert in certs:
        cert_name = (cert.get("certification_name") or "").strip()
        cert_name_norm = _normalize_text(cert_name)
        if cert_name_norm and cert_name_norm in normalized_message:
            return cert

    msg_tokens = _tokenize(message)
    best = None
    best_score = 0
    for cert in certs:
        cert_name = cert.get("certification_name") or ""
        cert_tokens = _tokenize(cert_name)
        score = len(msg_tokens & cert_tokens)
        if score > best_score:
            best = cert
            best_score = score

    return best if best_score > 0 else None


def _extract_type_hint(message: str) -> str:
    msg = message.lower()
    if "cbt" in msg:
        return "cbt"
    if "ilearn" in msg:
        return "ilearn"
    if "xylem" in msg:
        return "xylem"
    return ""


def _detect_cert_intent(message: str) -> str:
    msg = message.lower()
    if "unassign" in msg or "remove" in msg:
        return "unassign"
    if "validate" in msg or "validation" in msg:
        return "validate"
    if ("assign" in msg or "assigned" in msg) and "unassign" not in msg and "remove" not in msg:
        return "assign"
    return ""


def _intent_ask_text(intent: str) -> str:
    if intent == "assign":
        return "Please share the certificate name you want to get assigned."
    if intent == "unassign":
        return "Please share the certificate name you want to unassign."
    return "Please share the certificate name you want to validate."


async def _get_pending_cert_flow(user_id: str) -> dict | None:
    session = await db.chat_sessions.find_one({"user_id": user_id})
    if not session:
        return None
    flow = session.get("cert_flow") or {}
    if flow.get("intent") in CERT_INTENTS and flow.get("awaiting_name"):
        return flow
    return None


async def _set_pending_cert_flow(user_id: str, intent: str):
    await db.chat_sessions.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "cert_flow": {
                    "intent": intent,
                    "awaiting_name": True,
                    "updated_at": datetime.utcnow(),
                },
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


async def _clear_pending_cert_flow(user_id: str):
    await db.chat_sessions.update_one(
        {"user_id": user_id},
        {"$unset": {"cert_flow": ""}, "$set": {"updated_at": datetime.utcnow()}},
        upsert=True,
    )


def _has_cert_name_in_message(message: str, certs: list[dict]) -> bool:
    if _extract_type_hint(message):
        return True
    return _best_matching_certificate(message, certs) is not None


def _resolve_cert_reply(intent: str, matched_cert: dict | None, message: str) -> str:
    if intent == "assign":
        if matched_cert:
            cert_name = matched_cert.get("certification_name", "this certificate")
            return f"The certificate '{cert_name}' already exists and is already assigned to you."
        return ASSIGN_CERT_REPLY

    if intent == "unassign":
        if matched_cert:
            return UNASSIGN_CERT_REPLY
        return "This certificate is not currently assigned to your profile, so there is nothing to unassign."

    # validate
    cert_type = _extract_type_hint(message)
    if not cert_type and matched_cert:
        cert_type = (matched_cert.get("certification_type") or "").strip().lower()

    if cert_type == "cbt":
        return VALIDATE_CBT_REPLY
    if cert_type in {"ilearn", "xylem"}:
        return "Your certification type is not CBT, so you do not require validation for this particular certificate."
    if matched_cert is None:
        return "I could not find this certificate in your assigned certifications. Please share the exact assigned certificate name."
    return "Please share the certification type (iLearn, Xylem, or CBT) so I can guide you for validation."


async def _handle_certification_usecase(message: str, user_id: str) -> str | None:
    msg = re.sub(r"\s+", " ", message.lower()).strip()
    if not msg:
        return None

    certs = await db.certifications.find({"user_id": user_id}).to_list(500)
    pending = await _get_pending_cert_flow(user_id)
    if pending:
        intent = pending.get("intent", "")
        matched_cert = _best_matching_certificate(msg, certs)
        reply = _resolve_cert_reply(intent, matched_cert, msg)
        await _clear_pending_cert_flow(user_id)
        return reply

    is_cert_query = any(k in msg for k in ["certificate", "certification", "validate", "validation", "assign", "unassign"])
    if not is_cert_query:
        return None

    intent = _detect_cert_intent(msg)
    if intent in CERT_INTENTS:
        matched_cert = _best_matching_certificate(msg, certs)
        has_name = _has_cert_name_in_message(msg, certs)
        if not has_name:
            await _set_pending_cert_flow(user_id, intent)
            return _intent_ask_text(intent)
        return _resolve_cert_reply(intent, matched_cert, msg)

    return None


async def _save_simple_turn(user_id: str, user_message: str, ai_reply: str):
    session = await db.chat_sessions.find_one({"user_id": user_id})
    messages = session.get("messages", []) if session else []
    messages.extend([
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": ai_reply},
    ])
    await db.chat_sessions.update_one(
        {"user_id": user_id},
        {"$set": {"messages": messages, "updated_at": datetime.utcnow()}},
        upsert=True,
    )


@router.get("/history")
async def get_history(user: dict = Depends(decode_token)):
    user_id = user["sub"]
    session = await db.chat_sessions.find_one({"user_id": user_id})
    if not session:
        return {"messages": []}
    # Return only user/assistant turns for the UI (skip tool messages)
    ui_messages = [m for m in session.get("messages", []) if m["role"] in ("user", "assistant") and m.get("content")]
    return {"messages": ui_messages}


@router.post("/")
async def chat(req: ChatRequest, user: dict = Depends(decode_token)):
    user_id = user["sub"]

    cert_reply = await _handle_certification_usecase(req.message, user_id)
    if cert_reply:
        await _save_simple_turn(user_id, req.message, cert_reply)
        return {"reply": cert_reply}

    agent = get_agent()

    session = await db.chat_sessions.find_one({"user_id": user_id})
    history = _deserialize_messages(session.get("messages", [])) if session else []
    history.append(HumanMessage(content=req.message))

    try:
        result = await agent.ainvoke({"messages": history, "user_id": user_id})
        new_messages = result["messages"]
        ai_reply = ""
        for m in reversed(new_messages):
            if isinstance(m, AIMessage) and m.content:
                ai_reply = m.content
                break
        ai_reply = _ensure_context_prefix(ai_reply, new_messages)
        all_messages = history + [m for m in new_messages if m not in history]
        serialized = _serialize_messages(all_messages)
        await db.chat_sessions.update_one(
            {"user_id": user_id},
            {"$set": {"messages": serialized, "updated_at": datetime.utcnow()}},
            upsert=True,
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        ai_reply = f"Error: {str(e)}"

    return {"reply": ai_reply}


@router.delete("/history")
async def clear_history(user: dict = Depends(decode_token)):
    await db.chat_sessions.delete_one({"user_id": user["sub"]})
    return {"cleared": True}
