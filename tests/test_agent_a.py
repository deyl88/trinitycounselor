"""
Tests for Agent A — Private Counselor for Partner A.

Integration tests require a running postgres + Neo4j instance.
Mark with @pytest.mark.integration to exclude from CI unit runs.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAgentAPrompt:
    def test_build_system_prompt_no_context(self):
        from backend.agents.prompts.agent_a import build_system_prompt

        prompt = build_system_prompt()
        assert "EFT" in prompt
        assert "Attachment" in prompt
        assert "IFS" in prompt
        assert "Gottman" in prompt
        assert "Esther Perel" in prompt
        assert "private" in prompt.lower()

    def test_build_system_prompt_with_context(self):
        from backend.agents.prompts.agent_a import build_system_prompt

        ctx = "Pattern: shows tendency toward emotional withdrawal"
        prompt = build_system_prompt(retrieved_context=ctx)
        assert ctx in prompt
        assert "previous sessions" in prompt


class TestAgentAChat:
    @pytest.mark.asyncio
    async def test_chat_returns_string(self):
        """Agent A chat should return a non-empty string response."""
        from backend.agents import agent_a

        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "messages": [MagicMock(type="ai", content="I hear you. That sounds really hard.")],
            "user_id": "test-user",
            "session_id": "test-session",
            "couple_id": None,
            "retrieved_context": "",
        }

        with patch.object(agent_a, "_graph", mock_graph):
            result = await agent_a.chat(
                user_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                user_message="I've been feeling really distant from my partner.",
            )

        assert isinstance(result, str)
        assert len(result) > 0


class TestAgentAPrivacyIsolation:
    def test_agent_a_has_no_agent_b_imports(self):
        """Agent A must not import anything from Agent B — isolation check."""
        import ast
        import pathlib

        source = pathlib.Path("backend/agents/agent_a.py").read_text()
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        assert not any("agent_b" in imp for imp in imports), (
            "Agent A must not import from Agent B"
        )
