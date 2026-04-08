"""Aggregates all v1 sub-routers."""

from fastapi import APIRouter

from app.api.v1 import agent_a, agent_b, agent_r, relationships

router = APIRouter(prefix="/v1")
router.include_router(agent_a.router)
router.include_router(agent_b.router)
router.include_router(agent_r.router)
router.include_router(relationships.router)
