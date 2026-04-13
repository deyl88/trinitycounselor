"""Pytest configuration and shared fixtures for Trinity backend tests."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.auth.jwt import create_access_token


@pytest.fixture
def partner_a_token() -> str:
    return create_access_token(
        user_id="test-user-a-uuid",
        partner_tag="partner_a",
        relationship_id="test-relationship-uuid",
    )


@pytest.fixture
def partner_b_token() -> str:
    return create_access_token(
        user_id="test-user-b-uuid",
        partner_tag="partner_b",
        relationship_id="test-relationship-uuid",
    )


@pytest.fixture
async def client():
    """Async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
