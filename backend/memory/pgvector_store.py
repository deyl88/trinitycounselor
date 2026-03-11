"""
Per-user semantic memory store backed by pgvector.

Each user gets an isolated vector namespace (collection name = user_id).
Embeddings are generated via OpenAI text-embedding-3-small.

This store is used for *long-term* cross-session memory:
  - Session summaries from past conversations
  - Abstracted pattern embeddings for retrieval

It is SEPARATE from LangGraph's PostgresSaver checkpointer, which handles
short-term within-session conversation state.

Privacy: Only already-abstracted text is stored here; raw conversation content
is never written to this store.
"""
import uuid

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from backend.config import settings


def _embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key,
    )


def get_user_vector_store(user_id: uuid.UUID) -> PGVector:
    """
    Return a PGVector store namespaced to a single user.

    collection_name acts as a logical namespace; data for different users
    is stored in the same table but filtered by collection.
    """
    return PGVector(
        embeddings=_embeddings(),
        collection_name=f"user_{user_id}",
        connection=settings.postgres_url,
        use_jsonb=True,
    )


async def add_session_memory(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    content: str,
    metadata: dict | None = None,
) -> None:
    """
    Embed and store a session summary / abstracted insight for future retrieval.
    Called by the Privacy Mediator after pattern synthesis.
    """
    store = get_user_vector_store(user_id)
    doc = Document(
        page_content=content,
        metadata={
            "session_id": str(session_id),
            "user_id": str(user_id),
            **(metadata or {}),
        },
    )
    await store.aadd_documents([doc])


async def retrieve_relevant_context(
    user_id: uuid.UUID,
    query: str,
    k: int = 4,
) -> str:
    """
    Retrieve the k most semantically relevant past memories for a query.
    Returns a formatted string for injection into the agent system prompt.
    """
    store = get_user_vector_store(user_id)
    results: list[Document] = await store.asimilarity_search(query, k=k)

    if not results:
        return ""

    lines = ["--- Relevant context from past sessions ---"]
    for i, doc in enumerate(results, 1):
        lines.append(f"[{i}] {doc.page_content.strip()}")
    lines.append("--- End of context ---")
    return "\n".join(lines)
