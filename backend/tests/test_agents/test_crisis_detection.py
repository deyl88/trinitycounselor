"""Crisis detection node tests."""

import pytest
from langchain_core.messages import HumanMessage

from app.agents.graph.nodes import crisis_check


@pytest.mark.asyncio
async def test_no_crisis_in_normal_message():
    state = {
        "messages": [HumanMessage(content="I feel a bit sad today.")],
        "user_id": "u1",
        "partner_id": "",
        "relationship_id": "r1",
        "agent_role": "agent_a",
        "partner_name": "Alex",
        "retrieved_memories": [],
        "therapeutic_summary": "",
        "response": "",
        "pending_sap_signals": [],
        "crisis_detected": False,
        "crisis_severity": 0.0,
    }
    result = await crisis_check(state)
    assert result["crisis_detected"] is False


@pytest.mark.asyncio
async def test_crisis_detected_for_suicidal_ideation():
    state = {
        "messages": [HumanMessage(content="I don't want to be here anymore. I've been thinking about ending my life.")],
        "user_id": "u1",
        "partner_id": "",
        "relationship_id": "r1",
        "agent_role": "agent_a",
        "partner_name": "Alex",
        "retrieved_memories": [],
        "therapeutic_summary": "",
        "response": "",
        "pending_sap_signals": [],
        "crisis_detected": False,
        "crisis_severity": 0.0,
    }
    result = await crisis_check(state)
    assert result["crisis_detected"] is True
    assert result["crisis_severity"] > 0.5


@pytest.mark.asyncio
async def test_crisis_response_contains_resources():
    from app.agents.graph.nodes import crisis_escalation, _CRISIS_RESPONSE

    state = {
        "messages": [HumanMessage(content="test")],
        "user_id": "u1",
        "partner_id": "",
        "relationship_id": "r1",
        "agent_role": "agent_a",
        "partner_name": "Alex",
        "retrieved_memories": [],
        "therapeutic_summary": "",
        "response": "normal response",
        "pending_sap_signals": [],
        "crisis_detected": True,
        "crisis_severity": 0.9,
    }
    result = await crisis_escalation(state)
    assert "988" in result["response"]
    assert "741741" in result["response"]
    # Crisis escalation must override the normal response
    assert result["response"] != "normal response"
