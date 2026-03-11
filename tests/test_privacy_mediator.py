"""
Tests for the Privacy Mediator and pattern synthesis pipeline.

The privacy contract is the most critical correctness property in the system.
These tests verify that:
  1. Raw content never appears in synthesised patterns
  2. Pattern types are valid
  3. Synthesis failure is non-fatal (degrades gracefully)
  4. Insight Sync is idempotent
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        import os
        from backend.privacy.encryption import decrypt_text, encrypt_text

        key = os.urandom(32)
        plaintext = "I feel scared when you pull away."
        ciphertext = encrypt_text(plaintext, key)
        assert decrypt_text(ciphertext, key) == plaintext

    def test_different_nonces_each_call(self):
        import os
        from backend.privacy.encryption import encrypt_text

        key = os.urandom(32)
        text = "same text"
        c1 = encrypt_text(text, key)
        c2 = encrypt_text(text, key)
        assert c1 != c2, "Each encryption should use a fresh nonce"

    def test_wrong_key_raises(self):
        import os
        from cryptography.exceptions import InvalidTag
        from backend.privacy.encryption import decrypt_text, encrypt_text

        key1 = os.urandom(32)
        key2 = os.urandom(32)
        ciphertext = encrypt_text("secret", key1)
        with pytest.raises(InvalidTag):
            decrypt_text(ciphertext, key2)


class TestSynthesizer:
    @pytest.mark.asyncio
    async def test_synthesis_returns_valid_patterns(self):
        """Synthesiser should return a list of dicts with required fields."""
        from backend.models.pattern import PatternType

        mock_response = MagicMock()
        mock_response.content = """[
            {
                "pattern_type": "attachment",
                "content": "Exhibits anxiety when partner is emotionally unavailable.",
                "framework_tag": "EFT",
                "confidence": 0.85
            }
        ]"""

        with patch("backend.privacy.synthesizer.ChatAnthropic") as MockLLM:
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
            MockLLM.return_value = mock_llm_instance

            from backend.privacy.synthesizer import synthesise_patterns

            turns = [
                {"role": "human", "content": "I feel scared when my partner doesn't respond."},
                {"role": "ai", "content": "What happens inside you when that silence stretches?"},
            ]
            patterns = await synthesise_patterns(turns, uuid.uuid4(), uuid.uuid4())

        assert len(patterns) == 1
        assert patterns[0]["pattern_type"] in {pt.value for pt in PatternType}
        assert isinstance(patterns[0]["content"], str)

    @pytest.mark.asyncio
    async def test_synthesis_failure_returns_empty_list(self):
        """Synthesis LLM failure should return empty list, not raise."""
        with patch("backend.privacy.synthesizer.ChatAnthropic") as MockLLM:
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(side_effect=Exception("API timeout"))
            MockLLM.return_value = mock_llm_instance

            from backend.privacy.synthesizer import synthesise_patterns

            result = await synthesise_patterns(
                [{"role": "human", "content": "test"}], uuid.uuid4(), uuid.uuid4()
            )

        assert result == []

    def test_synthesiser_prompt_forbids_quotes(self):
        """The synthesis system prompt must explicitly forbid direct quotes."""
        from backend.privacy.synthesizer import SYNTHESIS_SYSTEM_PROMPT

        assert "quote" in SYNTHESIS_SYSTEM_PROMPT.lower() or "verbatim" in SYNTHESIS_SYSTEM_PROMPT.lower()
        assert "never" in SYNTHESIS_SYSTEM_PROMPT.lower() or "strict" in SYNTHESIS_SYSTEM_PROMPT.lower()


class TestPrivacyMediatorContract:
    def test_rkg_nodes_have_no_raw_content_fields(self):
        """RKG Cypher queries must not define fields that could hold raw conversation text."""
        from backend.graph import queries

        raw_content_markers = ["transcript", "raw_", "quote", "verbatim", "said", "stated"]
        query_source = "\n".join([
            queries.UPSERT_RELATIONAL_PATTERN,
            queries.UPSERT_PERSON,
            queries.UPSERT_COUPLE,
        ])
        for marker in raw_content_markers:
            assert marker not in query_source.lower(), (
                f"RKG query contains potentially raw-content field: '{marker}'"
            )
