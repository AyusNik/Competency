from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.database import db
from datetime import datetime
from typing import Dict, List
from jose import jwt, JWTError
import os, smtplib, asyncio
from email.mime.text import MIMEText
from functools import partial

router = APIRouter(tags=["Manager Chat"])

rooms: Dict[str, List[dict]] = {}

CAT_SECRET = os.getenv("CAT_JWT_SECRET", "cat_secret_key")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
MANAGER_PORTAL_URL = os.getenv("MANAGER_PORTAL_URL", "http://localhost:4200/manager-chat")


def _decode_manager_email(token: str) -> str:
    try:
        payload = jwt.decode(token, CAT_SECRET, algorithms=["HS256"])
        return payload.get("email", "")
    except JWTError:
        return ""


def _send_chat_email(manager_email: str, user_name: str, room_id: str):
    try:
        body = f"""Hi,

{user_name} has initiated a live chat and is waiting to speak with you.

Click the link below to join the chat:
{MANAGER_PORTAL_URL}

Room ID: {room_id}

Please respond at your earliest convenience.

— MyPCP System"""
        msg = MIMEText(body)
        msg["Subject"] = f"[MyPCP] {user_name} wants to chat with you"
        msg["From"] = SENDER_EMAIL
        msg["To"] = manager_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_USER, EMAIL_PASS)
            s.sendmail(SENDER_EMAIL, manager_email, msg.as_string())
    except Exception as e:
        print(f"Email send failed: {e}")


async def _save_message(room_id: str, sender: str, role: str, content: str):
    await db.manager_chat_rooms.update_one(
        {"room_id": room_id},
        {"$push": {"messages": {"sender": sender, "role": role, "content": content, "ts": datetime.utcnow().isoformat()}},
         "$set": {"updated_at": datetime.utcnow()}},
        upsert=True
    )


@router.get("/manager-chat/history/{room_id}")
async def get_room_history(room_id: str):
    room = await db.manager_chat_rooms.find_one({"room_id": room_id})
    return {"messages": room.get("messages", []) if room else []}


@router.delete("/manager-chat/room/{room_id}")
async def delete_room(room_id: str):
    # Close any active WS connections in memory
    if room_id in rooms:
        for conn in list(rooms[room_id]):
            try:
                await conn["ws"].send_json({"type": "status", "content": "Manager has left. Chat ended."})
                await conn["ws"].close()
            except Exception:
                pass
        del rooms[room_id]
    await db.manager_chat_rooms.delete_one({"room_id": room_id})
    return {"deleted": True}


@router.get("/manager-chat/rooms")
async def get_all_rooms(token: str = Query(...)):
    manager_email = _decode_manager_email(token)
    # Get all user_ids assigned to this manager
    assigned = await db.user_managers.find({"manager_email": manager_email}).to_list(500)
    assigned_user_ids = {a["user_id"] for a in assigned}

    rooms_list = await db.manager_chat_rooms.find().to_list(200)
    result = []
    for r in rooms_list:
        if r["room_id"] not in assigned_user_ids:
            continue
        msgs = r.get("messages", [])
        result.append({
            "room_id": r["room_id"],
            "user_name": r.get("user_name") or r["room_id"][:12],
            "last_message": msgs[-1]["content"] if msgs else "No messages yet",
            "last_ts": msgs[-1]["ts"] if msgs else "",
            "last_role": msgs[-1]["role"] if msgs else "",
            "online": r["room_id"] in rooms,
        })
    return result

@router.websocket("/ws/manager-chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, role: str = Query(...), name: str = Query(...)):
    await websocket.accept()
    if room_id not in rooms:
        rooms[room_id] = []
    conn = {"ws": websocket, "role": role, "name": name}
    rooms[room_id].append(conn)

    # Save room with user name — only set user_name when role is user, never overwrite with None
    update_fields = {"room_id": room_id, "updated_at": datetime.utcnow()}
    if role == "user":
        update_fields["user_name"] = name
    await db.manager_chat_rooms.update_one(
        {"room_id": room_id},
        {"$set": update_fields},
        upsert=True
    )

    # Send email to manager once per room when user connects
    if role == "user":
        room_doc = await db.manager_chat_rooms.find_one({"room_id": room_id})
        if not room_doc or not room_doc.get("email_sent"):
            mgr = await db.user_managers.find_one({"user_id": room_id})
            if mgr and mgr.get("manager_email"):
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, partial(_send_chat_email, mgr["manager_email"], name, room_id))
            await db.manager_chat_rooms.update_one(
                {"room_id": room_id},
                {"$set": {"email_sent": True}},
                upsert=True
            )

    # Send history on connect
    room = await db.manager_chat_rooms.find_one({"room_id": room_id})
    history = room.get("messages", []) if room else []
    await websocket.send_json({"type": "history", "messages": history})

    # Notify others that someone joined
    for c in rooms[room_id]:
        if c["ws"] != websocket:
            await c["ws"].send_json({"type": "status", "content": f"{name} joined the chat"})

    try:
        while True:
            data = await websocket.receive_text()
            msg = {"type": "message", "sender": name, "role": role, "content": data,
                   "ts": datetime.utcnow().isoformat()}
            await _save_message(room_id, name, role, data)
            for c in rooms[room_id]:
                await c["ws"].send_json(msg)
    except WebSocketDisconnect:
        rooms[room_id].remove(conn)
        if role == "manager":
            # Manager left — notify remaining users, delete room from DB
            for c in list(rooms.get(room_id, [])):
                try:
                    await c["ws"].send_json({"type": "status", "content": "Manager has left. Chat ended."})
                except Exception:
                    pass
            if room_id in rooms:
                del rooms[room_id]
            await db.manager_chat_rooms.delete_one({"room_id": room_id})
        else:
            # User left — notify manager, delete room from DB
            for c in list(rooms.get(room_id, [])):
                try:
                    await c["ws"].send_json({"type": "status", "content": f"{name} has left. Chat ended."})
                except Exception:
                    pass
            if room_id in rooms:
                del rooms[room_id]
            await db.manager_chat_rooms.delete_one({"room_id": room_id})
