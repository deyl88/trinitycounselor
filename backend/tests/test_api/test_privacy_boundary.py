"""Privacy boundary tests — verifies that agents cannot cross namespace barriers."""

import pytest


@pytest.mark.asyncio
async def test_partner_b_cannot_call_agent_a(client, partner_b_token):
    """Partner B's JWT must be rejected by the Agent A endpoint."""
    response = await client.post(
        "/v1/agent-a/chat",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {partner_b_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_partner_a_cannot_call_agent_b(client, partner_a_token):
    """Partner A's JWT must be rejected by the Agent B endpoint."""
    response = await client.post(
        "/v1/agent-b/chat",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {partner_a_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_agent_a_rejected(client):
    """Requests without a JWT must be rejected with 401."""
    response = await client.post("/v1/agent-a/chat", json={"message": "hello"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_agent_b_rejected(client):
    response = await client.post("/v1/agent-b/chat", json={"message": "hello"})
    assert response.status_code == 401
