"""API router registry."""

from fastapi import APIRouter

from backend.api.analyze import router as analyze_router
from backend.api.execution import router as execution_router
from backend.api.health import router as health_router
from backend.api.validation import validation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analyze_router)
api_router.include_router(execution_router)
api_router.include_router(validation_router)
