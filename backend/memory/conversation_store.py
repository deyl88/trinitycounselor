"""
Conversation history persistence.

Provides helpers to read/write encrypted Message records from postgres.
The LangGraph checkpointer handles live in-session state; this module provides
a human-readable, queryable audit log of all messages per session.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.keys import decrypt_user_key
from backend.models.message import Message, MessageRole
from backend.privacy.encryption import decrypt_text, encrypt_text


async def save_message(
    db: AsyncSession,
    session_id: uuid.UUID,
    role: MessageRole,
    content: str,
    user_key_encrypted: str,
    token_count: int | None = None,
) -> Message:
    """Encrypt and persist a single message turn."""
    user_key = decrypt_user_key(user_key_encrypted)
    content_encrypted = encrypt_text(content, user_key)

    msg = Message(
        session_id=session_id,
        role=role.value,
        content_encrypted=content_encrypted,
        token_count=token_count,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def load_messages(
    db: AsyncSession,
    session_id: uuid.UUID,
    user_key_encrypted: str,
) -> list[dict]:
    """
    Load and decrypt all messages for a session, ordered chronologically.
    Returns list of {"role": str, "content": str} dicts.
    """
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    user_key = decrypt_user_key(user_key_encrypted)
    return [
        {"role": m.role, "content": decrypt_text(m.content_encrypted, user_key)}
        for m in messages
    ]
