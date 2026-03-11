"""
Tests for the Relational Knowledge Graph (RKG) client and queries.

Unit tests mock the Neo4j driver. Integration tests require a live instance.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRKGClientUnit:
    @pytest.mark.asyncio
    async def test_upsert_pattern_returns_id(self):
        """upsert_pattern should return the pattern_id string."""
        from backend.graph.rkg_client import RKGClient
        from backend.models.pattern import AbstractedPattern

        pattern = AbstractedPattern(
            user_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            pattern_type="attachment",
            content="Exhibits avoidant tendencies under relational stress.",
            framework_tag="EFT",
            confidence=0.9,
        )

        mock_driver = MagicMock()
        mock_session = AsyncMock()
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_session.run = AsyncMock()

        client = RKGClient(driver=mock_driver)
        result = await client.upsert_pattern(
            user_id=uuid.uuid4(),
            couple_id=None,
            pattern=pattern,
        )

        assert isinstance(result, str)
        assert result == str(pattern.id)

    @pytest.mark.asyncio
    async def test_get_relationship_summary_returns_dict(self):
        """get_relationship_summary should return a dict even with no data."""
        from backend.graph.rkg_client import RKGClient

        mock_driver = MagicMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

        client = RKGClient(driver=mock_driver)
        summary = await client.get_relationship_summary(uuid.uuid4())

        assert "patterns" in summary
        assert "events" in summary
        assert "partners" in summary


class TestAgentRPrompt:
    def test_build_system_prompt_no_rkg(self):
        from backend.agents.prompts.agent_r import build_system_prompt

        prompt = build_system_prompt(rkg_context=None)
        assert "third presence" in prompt.lower() or "Relationship Counselor" in prompt
        assert "private" in prompt.lower()
        assert "No prior relational data" in prompt

    def test_build_system_prompt_with_rkg_context(self):
        from backend.agents.prompts.agent_r import build_system_prompt

        ctx = {
            "primary_cycle": "pursue-withdraw",
            "eft_stage": "de-escalation",
            "patterns": [
                {
                    "type": "conflict",
                    "description": "recurring escalation around proximity needs",
                    "framework": "EFT",
                    "confidence": 0.9,
                }
            ],
            "partners": [],
            "events": [],
        }
        prompt = build_system_prompt(rkg_context=ctx)
        assert "pursue-withdraw" in prompt
        assert "de-escalation" in prompt
        assert "proximity needs" in prompt
