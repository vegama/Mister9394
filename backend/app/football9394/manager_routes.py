from __future__ import annotations

from fastapi import APIRouter

from .career_routes import router as career_router
from .management_routes import router as management_router
from .match_market_routes import router as match_market_router
from .world_routes import router as world_router
from .manager_route_support import _career_store, _load_manager_career

router = APIRouter()
router.include_router(career_router)
router.include_router(management_router)
router.include_router(match_market_router)
router.include_router(world_router)

__all__ = ["router", "_career_store", "_load_manager_career"]
