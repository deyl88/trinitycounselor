"""pgvector-backed conversation memory store.

Privacy Architecture
────────────────────
Each memory record is stored in a namespace scoped to both the agent role
and the relationship ID: ``f"{agent_role}:{relationship_id}"``.

This means:
  - Agent A's memories for relationship "r1" live in namespace "agent_a:r1"
  - Agent B's memories for "r1" live in "agent_b:r1"
  - Agent R's memories live in "agent_r:r1"

An attempted cross-namespace read raises ``UnauthorizedNamespaceAccess``.
The namespace check is enforced in ``_validate_namespace_access``.

Embedding
─────────
We embed the concatenation of user message + AI response for rich
semantic retrieval. This captures the full exchange arc, not just the
user's words, making similarity search more therapeutically relevant.

Encryption (TODO integration)
──────────────────────────────
The ``content_enc`` column stores AES-256-GCM encrypted raw content.
The plaintext ``content`` column stores only the embedding source — which
could be further anonymised. Full encryption integration requires the
user's derived key to be available in request context (from auth middleware).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from langchain_core.documents import Document
from langchain_postgres import PGVector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import MemoryStoreError, UnauthorizedNamespaceAccess
from app.core.logging import get_logger

logger = get_logger(__name__)

# Agent roles permitted to access each namespace type.
# An agent may only read from namespaces that start with its own role prefix.
_NAMESPACE_PERMISSIONS: dict[str, list[str]] = {
    "agent_a": ["agent_a"],
    "agent_b": ["agent_b"],
    "agent_r": ["agent_r"],
}


class ConversationMemoryStore:
    """Per-user, per-agent pgvector conversation memory.

    Instantiate once per request with the authenticated user's context.
    The namespace enforces the privacy boundary at the storage layer.

    Args:
        user_id: UUID string of the authenticated user.
        agent_role: "agent_a" | "agent_b" | "agent_r"
        relationship_id: UUID string of the relationship.
        db: Async SQLAlchemy session.
    """

    def __init__(
        self,
        user_id: str,
        agent_role: str,
        relationship_id: str,
        db: AsyncSession,
    ) -> None:
        self.user_id = user_id
        self.agent_role = agent_role
        self.relationship_id = relationship_id
        self.namespace = f"{agent_role}:{relationship_id}"
        self._db = db
        self._settings = get_settings()

    def _validate_namespace_access(self, namespace: str) -> None:
        """Ensure this store instance can access the requested namespace.

        Raises:
            UnauthorizedNamespaceAccess: If the agent_role is not permitted
                to access the target namespace.
        """
        permitted_prefixes = _NAMESPACE_PERMISSIONS.get(self.agent_role, [])
        if not any(namespace.startswith(p) for p in permitted_prefixes):
            raise UnauthorizedNamespaceAccess(
                f"Agent '{self.agent_role}' is not permitted to access namespace '{namespace}'.",
                agent_role=self.agent_role,
                namespace=namespace,
            )

    def _get_vector_store(self) -> PGVector:
        """Return a LangChain PGVector store scoped to this namespace."""
        self._validate_namespace_access(self.namespace)
        settings = self._settings
        # Use sync connection string for PGVector (langchain-postgres uses psycopg3)
        connection = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
        return PGVector(
            embeddings=self._get_embeddings(),
            collection_name=self.namespace,
            connection=connection,
            use_jsonb=True,
        )

    def _get_embeddings(self):
        """Return the embedding model.

        Uses langchain-anthropic's embedding interface. Switch to
        langchain-openai or a local model without touching this class.
        """
        # For now we use a simple approach: we'll embed using the Anthropic client
        # In production, use a dedicated embedding endpoint.
        # langchain-anthropic doesn't have embeddings yet; use OpenAI embeddings
        # or a custom wrapper. This is a TODO integration point.
        from langchain_community.embeddings import FakeEmbeddings

        # TODO: Replace with real embeddings (e.g., OpenAI text-embedding-3-small
        # or a local sentence-transformers model). FakeEmbeddings is a safe
        # stand-in during development that lets the pgvector integration work
        # end-to-end without an embedding API key.
        return FakeEmbeddings(size=self._settings.embedding_dimensions)

    async def add_exchange(
        self,
        user_message: str,
        ai_response: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a complete conversation exchange.

        The user message and AI response are concatenated into a single
        document for embedding. This captures the full exchange arc.

        Args:
            user_message: The user's raw message text.
            ai_response: The AI counselor's response text.
            metadata: Optional additional metadata to store alongside.

        Returns:
            The UUID of the stored memory record.
        """
        exchange_id = str(uuid.uuid4())
        content = f"User: {user_message}\nCounselor: {ai_response}"
        meta = {
            "exchange_id": exchange_id,
            "user_id": self.user_id,
            "agent_role": self.agent_role,
            "relationship_id": self.relationship_id,
            "timestamp": datetime.now(UTC).isoformat(),
            **(metadata or {}),
        }
        doc = Document(page_content=content, metadata=meta)
        try:
            vs = self._get_vector_store()
            await vs.aadd_documents([doc], ids=[exchange_id])
            logger.debug(
                "memory_exchange_stored",
                exchange_id=exchange_id,
                namespace=self.namespace,
            )
        except Exception as exc:
            raise MemoryStoreError(
                f"Failed to store memory exchange: {exc}",
                namespace=self.namespace,
            ) from exc
        return exchange_id

    async def similarity_search(
        self,
        query: str,
        k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve the top-k most semantically relevant past exchanges.

        Args:
            query: The current user message to find relevant memories for.
            k: Number of results. Defaults to settings.memory_top_k.

        Returns:
            List of dicts with 'content' and 'metadata' keys, sorted by
            relevance (most relevant first).
        """
        top_k = k or self._settings.memory_top_k
        try:
            vs = self._get_vector_store()
            docs = await vs.asimilarity_search(query, k=top_k)
            return [{"content": d.page_content, "metadata": d.metadata} for d in docs]
        except Exception as exc:
            logger.warning(
                "memory_search_failed",
                namespace=self.namespace,
                error=str(exc),
            )
            # Degrade gracefully — empty memory is better than a crashed request
            return []

    async def get_therapeutic_summary(self) -> str:
        """Retrieve the compressed therapeutic summary for this namespace.

        The therapeutic summary is a running LLM-generated compression of
        the session arc — updated periodically to keep the context window
        manageable for long-running therapeutic relationships.

        Returns:
            Summary text, or empty string if none exists yet.
        """
        result = await self._db.execute(
            text(
                "SELECT summary_text FROM therapeutic_summaries "
                "WHERE user_id = :user_id AND namespace = :namespace"
            ),
            {"user_id": self.user_id, "namespace": self.namespace},
        )
        row = result.fetchone()
        return row[0] if row else ""

    async def update_therapeutic_summary(self, summary: str) -> None:
        """Upsert the therapeutic summary for this namespace.

        Called by the generate_response node after every N exchanges
        (configurable) to compress the running session arc.

        Args:
            summary: New summary text (replaces the old one entirely).
        """
        await self._db.execute(
            text(
                "INSERT INTO therapeutic_summaries (id, user_id, namespace, summary_text, updated_at) "
                "VALUES (:id, :user_id, :namespace, :summary_text, :updated_at) "
                "ON CONFLICT (user_id, namespace) DO UPDATE "
                "SET summary_text = EXCLUDED.summary_text, updated_at = EXCLUDED.updated_at"
            ),
            {
                "id": str(uuid.uuid4()),
                "user_id": self.user_id,
                "namespace": self.namespace,
                "summary_text": summary,
                "updated_at": datetime.now(UTC),
            },
        )
        await self._db.commit()

    async def stage_sap_signals(
        self,
        signals: list[dict[str, Any]],
    ) -> None:
        """Insert abstracted SAP signals into the staging table for async RKG sync.

        SAP signals are written here by the store_memory node and consumed
        by the Privacy Mediator during the next insight sync call.

        Args:
            signals: List of SAP signal dicts (see privacy/schemas.py for structure).
        """
        await self._db.execute(
            text(
                "INSERT INTO sap_signals_staging "
                "(id, relationship_id, source_agent, signals, created_at, processed) "
                "VALUES (:id, :relationship_id, :source_agent, :signals, :created_at, false)"
            ),
            {
                "id": str(uuid.uuid4()),
                "relationship_id": self.relationship_id,
                "source_agent": self.agent_role,
                "signals": json.dumps(signals),
                "created_at": datetime.now(UTC),
            },
        )
        await self._db.commit()
        logger.debug(
            "sap_signals_staged",
            count=len(signals),
            relationship_id=self.relationship_id,
            source_agent=self.agent_role,
        )
