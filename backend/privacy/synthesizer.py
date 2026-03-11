"""
Pattern Synthesizer — abstracts raw conversation content into privacy-safe patterns.

Called by the Privacy Mediator after a solo session closes.
Uses Claude to extract themes, attachment signals, and relational dynamics
WITHOUT preserving any direct quotes or identifiable specifics.

Output contract (enforced by prompt + validation):
  - No direct quotes from the conversation
  - No names, locations, or identifiable details
  - Describes patterns, not events ("shows tendency to…" not "said that…")
  - Mapped to a PatternType and therapy framework tag
"""
import json
import uuid

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import settings
from backend.models.pattern import PatternType

SYNTHESIS_SYSTEM_PROMPT = """
You are a clinical pattern analyst for a relationship counseling AI system.

Your job is to read a therapy conversation and extract ABSTRACTED PATTERNS ONLY.

STRICT PRIVACY RULES — you must follow these without exception:
1. Never quote the conversation directly. No verbatim phrases.
2. Never include names, locations, dates, or any identifiable detail.
3. Describe patterns and tendencies, not specific events or statements.
4. Write as if describing a psychological profile observation, not a transcript.

Output FORMAT — return ONLY a valid JSON array. No other text. Each element:
{
  "pattern_type": one of: attachment | emotional | communication | need | conflict | repair | breakthrough | trigger,
  "content": "A one-to-two sentence abstract description of the pattern observed.",
  "framework_tag": one of: EFT | Gottman | IFS | Attachment | Esther_Perel | FamilySystems | null,
  "confidence": float between 0.0 and 1.0
}

Extract between 1 and 6 patterns. Be precise. Be clinically grounded.
""".strip()


async def synthesise_patterns(
    conversation_turns: list[dict],  # [{"role": "human"|"ai", "content": str}]
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> list[dict]:
    """
    Given the decrypted conversation turns, return a list of abstracted pattern dicts.
    Each dict maps to an AbstractedPattern model.

    Returns an empty list if synthesis fails (degraded gracefully).
    """
    if not conversation_turns:
        return []

    # Format conversation for the synthesiser
    formatted = "\n".join(
        f"[{t['role'].upper()}]: {t['content']}" for t in conversation_turns
    )

    llm = ChatAnthropic(
        model=settings.claude_model,
        anthropic_api_key=settings.anthropic_api_key,
        temperature=0.2,
        max_tokens=1500,
    )

    messages = [
        SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(content=f"Conversation to analyse:\n\n{formatted}"),
    ]

    try:
        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        patterns = json.loads(raw)

        # Validate pattern_type values
        valid_types = {pt.value for pt in PatternType}
        validated = [
            p for p in patterns
            if isinstance(p, dict)
            and p.get("pattern_type") in valid_types
            and isinstance(p.get("content"), str)
            and len(p["content"]) > 10
        ]
        return validated

    except Exception:  # noqa: BLE001
        # Synthesis failures are non-fatal — session still closes cleanly
        return []
