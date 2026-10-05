"""
routers/conversations_router.py
Conversation CRUD and message loading.
"""

import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"


@router.get("")
def list_conversations(current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY created_at DESC",
        (current_user["user_id"],),
    )
    rows = cursor.fetchall()
    conn.close()
    return {"conversations": [dict(r) for r in rows]}


@router.post("")
def create_conversation(
    req: CreateConversationRequest,
    current_user: dict = Depends(get_current_user),
):
    conn = get_db()
    cursor = conn.cursor()
    conv_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
        (conv_id, current_user["user_id"], req.title),
    )
    conn.commit()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return {"conversation": row}


@router.get("/{conv_id}")
def get_conversation(conv_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
        (conv_id, current_user["user_id"]),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"conversation": dict(row)}


@router.get("/{conv_id}/messages")
def get_messages(conv_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()

    # Verify ownership
    cursor.execute(
        "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
        (conv_id, current_user["user_id"]),
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Conversation not found.")

    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        msg = dict(row)
        # Deserialize JSON fields
        for field in ("citations", "sources"):
            if msg.get(field):
                try:
                    msg[field] = json.loads(msg[field])
                except Exception:
                    msg[field] = []
            else:
                msg[field] = []
        messages.append(msg)

    return {"messages": messages}


@router.delete("/{conv_id}")
def delete_conversation(conv_id: str, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM conversations WHERE id = ? AND user_id = ?",
        (conv_id, current_user["user_id"]),
    )
    conn.commit()
    conn.close()
    return {"message": "Conversation deleted."}
