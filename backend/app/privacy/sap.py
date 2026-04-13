"""Signal Abstraction Protocol (SAP) — the privacy firewall's extraction engine.

The SAP transforms raw private conversation exchanges into abstracted
categorical signals. This is the ONLY mechanism by which information
crosses from the private layer to the shared Relational Knowledge Graph.

Privacy Invariants (enforced here)
────────────────────────────────────
1. Input: (user_message, ai_response) — raw private content
2. Output: list[SAPSignal] — themes, intensities, categories ONLY
3. The LLM is instructed never to include quotes, names, or specifics
4. The SAPSignal validator rejects themes that look too specific
5. The output is parsed and re-serialized — no raw LLM text passes through

Status: STUB — the interface, schema validation, and prompt are fully
implemented. The LLM extraction call is wired but requires
ANTHROPIC_API_KEY in the environment to run.
"""

from __future__ import annotations

import json

from anthropic import AsyncAnthropic

from app.agents.prompts.sap_system import SAP_SYSTEM_PROMPT
from app.config import get_settings
from app.core.logging import get_logger
from app.privacy.schemas import SAPSignal

logger = get_logger(__name__)


class SignalAbstractionProtocol:
    """Extracts abstracted relational signals from a private conversation exchange.

    Instantiate per-extraction call (lightweight — just holds config).
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = AsyncAnthropic(api_key=self._settings.anthropic_api_key)

    async def extract(
        self,
        user_message: str,
        ai_response: str,
        source_agent: str,
    ) -> list[SAPSignal]:
        """Extract SAP signals from a private exchange.

        Args:
            user_message: The partner's raw message (private content).
            ai_response: The counselor's response (private content).
            source_agent: "agent_a" or "agent_b" — determines source_tag.

        Returns:
            List of validated SAPSignal objects. Empty list if extraction
            fails or the exchange contains no meaningful relational signal.

        Privacy guarantee:
            The LLM call uses a strictly-structured prompt that forbids
            quotes, names, and identifying content. Output is parsed and
            re-serialized through SAPSignal validators before leaving
            this function — no raw LLM text propagates downstream.
        """
        source_tag = "partner_a" if source_agent == "agent_a" else "partner_b"
        user_content = self._build_extraction_prompt(user_message, ai_response, source_tag)

        try:
            response = await self._client.messages.create(
                model=self._settings.llm_model,
                max_tokens=512,
                system=SAP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )

            raw_text = response.content[0].text.strip()
            return self._parse_signals(raw_text, source_tag)

        except Exception as exc:
            logger.warning(
                "sap_extraction_error",
                source_agent=source_agent,
                error=str(exc),
            )
            # Fail open — return no signals rather than blocking the conversation
            return []

    def _build_extraction_prompt(
        self,
        user_message: str,
        ai_response: str,
        source_tag: str,
    ) -> str:
        """Build the user-turn content for the SAP extraction call."""
        return (
            f"Source partner tag: {source_tag}\n\n"
            f"--- EXCHANGE START ---\n"
            f"Partner: {user_message}\n\n"
            f"Counselor: {ai_response}\n"
            f"--- EXCHANGE END ---\n\n"
            f"Extract relational signals from this exchange. "
            f"Remember: no quotes, no names, no specifics. JSON only."
        )

    def _parse_signals(self, raw_text: str, source_tag: str) -> list[SAPSignal]:
        """Parse and validate the LLM's JSON output into SAPSignal objects.

        Strips markdown code fences if present, parses JSON, validates
        each signal through the SAPSignal Pydantic model.

        Returns an empty list on any parse or validation failure.
        """
        # Strip optional markdown code fences
        text = raw_text
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            raw_signals = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning("sap_json_parse_failed", error=str(exc), raw=text[:200])
            return []

        if not isinstance(raw_signals, list):
            logger.warning("sap_expected_list", got=type(raw_signals).__name__)
            return []

        signals = []
        for raw in raw_signals:
            try:
                # Inject source_tag from our validated context, not from LLM output
                raw["source_tag"] = source_tag
                signal = SAPSignal(**raw)
                signals.append(signal)
            except Exception as exc:
                logger.warning("sap_signal_validation_failed", error=str(exc), raw=raw)
                continue

        logger.debug("sap_signals_extracted", count=len(signals), source_tag=source_tag)
        return signals
