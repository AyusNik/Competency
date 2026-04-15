from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.database import db
from app.auth import decode_token
from app.agent import get_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from datetime import datetime

import json

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str


def _extract_context_sentence(new_messages: list) -> str:
    """Extract the display_message or build the context sentence from tool results."""
    # First pass: collect all tool results for context
    training_name = ""
    element_name = ""
    unit_name = ""

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
                return f"The assessment for **'{unit}'** is currently locked. To get access or resolve this, please contact your Business Line Manager."

        # Training has no courses
        if "has_courses" in data and "training_name" in data:
            if not data.get("has_courses"):
                training_name = data.get("training_name", "this training")

        # Validate element — capture matched element name
        if "matched_name" in data and data.get("valid") and "available_elements" not in data:
            element_name = data.get("matched_name", "")

        # Validate unit — capture matched unit name
        if "matched_name" in data and data.get("valid") and "available_units" not in data and not element_name:
            unit_name = data.get("matched_name", "")

    # Build no-courses sentence if training has no courses
    if training_name:
        parts = [f"No courses are yet mapped to the training **'{training_name}'**"]
        if element_name:
            parts.append(f"for the competency element **'{element_name}'**")
        parts.append(". To resolve this, please contact your Business Line Manager.")
        return " ".join(parts)

    return ""


def _ensure_context_prefix(ai_reply: str, new_messages: list) -> str:
    """If the reply starts directly with manager details, prepend the context sentence."""
    manager_starters = [
        "**your business line manager",
        "here are your business line",
        "**name:**",
        "- **name:**",
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
