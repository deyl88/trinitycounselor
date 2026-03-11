"""
Privacy Mediator — the enforcement layer between private stores and the RKG.

Responsibilities:
  1. Triggered when a solo session closes.
  2. Loads and decrypts the session's message history.
  3. Calls the Synthesizer to extract abstract patterns (no raw content passes through).
  4. Persists AbstractedPattern records to postgres.
  5. Embeds synthesised summaries into the user's pgvector store (long-term memory).
  6. Writes patterns to the Neo4j RKG via the RKG client.
  7. Marks the session as insight_synced = True.

PRIVACY GUARANTEE: Raw message content is decrypted only within this module,
used only for synthesis, and immediately discarded. It never flows into the RKG,
pgvector, or any cross-partner context.
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.keys import decrypt_user_key
from backend.graph.rkg_client import RKGClient
from backend.memory.conversation_store import load_messages
from backend.memory.pgvector_store import add_session_memory
from backend.models.pattern import AbstractedPattern
from backend.models.session import Session, SessionStatus
from backend.models.user import User
from backend.privacy.synthesizer import synthesise_patterns


class PrivacyMediator:
    """
    Orchestrates the Insight Sync pipeline for a closed solo session.
    Instantiate per-request; do not share state across calls.
    """

    def __init__(self, db: AsyncSession, rkg: RKGClient) -> None:
        self.db = db
        self.rkg = rkg

    async def run_insight_sync(self, session_id: uuid.UUID) -> int:
        """
        Run the full Insight Sync pipeline for a session.
        Returns the number of patterns extracted and persisted.
        """
        session = await self._load_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found.")
        if session.insight_synced:
            return 0  # Idempotent

        user = await self._load_user(session.user_id)

        # Step 1: Load and decrypt raw conversation (ephemeral — used only here)
        turns = await load_messages(self.db, session_id, user.encrypted_key)

        # Step 2: Synthesise abstract patterns (LLM call — no raw content escapes)
        raw_patterns = await synthesise_patterns(turns, session.user_id, session_id)

        # Step 3: Persist AbstractedPattern records
        patterns: list[AbstractedPattern] = []
        for p in raw_patterns:
            pattern = AbstractedPattern(
                user_id=session.user_id,
                session_id=session_id,
                pattern_type=p["pattern_type"],
                content=p["content"],
                framework_tag=p.get("framework_tag"),
                confidence=float(p.get("confidence", 1.0)),
            )
            self.db.add(pattern)
            patterns.append(pattern)

        await self.db.flush()  # get IDs before RKG write

        # Step 4: Embed a session summary into the user's pgvector store
        if patterns:
            summary = self._build_summary(patterns)
            await add_session_memory(
                user_id=session.user_id,
                session_id=session_id,
                content=summary,
                metadata={"pattern_count": len(patterns)},
            )

        # Step 5: Write patterns to the RKG
        couple_id = session.couple_id
        for pattern in patterns:
            rkg_node_id = await self.rkg.upsert_pattern(
                user_id=session.user_id,
                couple_id=couple_id,
                pattern=pattern,
            )
            pattern.rkg_synced = True
            pattern.rkg_node_id = rkg_node_id

        # Step 6: Mark session synced
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(insight_synced=True)
        )
        await self.db.commit()

        return len(patterns)

    def _build_summary(self, patterns: list[AbstractedPattern]) -> str:
        """Build a plain-text summary of patterns for pgvector embedding."""
        lines = [f"Session pattern summary ({len(patterns)} patterns observed):"]
        for p in patterns:
            tag = f" [{p.framework_tag}]" if p.framework_tag else ""
            lines.append(f"- [{p.pattern_type.upper()}{tag}] {p.content}")
        return "\n".join(lines)

    async def _load_session(self, session_id: uuid.UUID) -> Session | None:
        result = await self.db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    async def _load_user(self, user_id: uuid.UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User {user_id} not found.")
        return user
