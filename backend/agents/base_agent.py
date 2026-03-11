"""
Base LangGraph agent scaffolding shared across Agent A, B, and R.

Provides:
  - Typed state definition
  - Async PostgresSaver checkpointer factory
  - Shared LLM instantiation
  - Thread ID convention: "{user_id}:{session_id}"
"""
import uuid
from typing import Annotated, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages

from backend.config import settings


class AgentState(TypedDict):
    """
    Shared state schema for all Trinity agents.

    `messages` uses the `add_messages` reducer — appends new messages
    rather than replacing the list on each node invocation.
    """
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_id: str
    couple_id: str | None
    retrieved_context: str  # injected by context retrieval node


def make_thread_config(user_id: uuid.UUID, session_id: uuid.UUID) -> RunnableConfig:
    """
    Build a LangGraph RunnableConfig that scopes the checkpointer
    to a specific user + session thread.
    """
    return {"configurable": {"thread_id": f"{user_id}:{session_id}"}}


def get_llm(temperature: float = 0.7, max_tokens: int = 2048) -> ChatAnthropic:
    """Shared LLM factory — all agents use the same model."""
    return ChatAnthropic(
        model=settings.claude_model,
        anthropic_api_key=settings.anthropic_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def get_checkpointer():
    """
    Return an async PostgresSaver checkpointer.
    The checkpointer persists LangGraph conversation state (messages + metadata)
    between requests, enabling stateful multi-turn conversations.

    Called once at agent compile time and reused across requests.
    """
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    # AsyncPostgresSaver uses psycopg3 connection string (not asyncpg)
    checkpointer = AsyncPostgresSaver.from_conn_string(settings.postgres_url)
    await checkpointer.setup()  # creates checkpoint tables if not present
    return checkpointer
