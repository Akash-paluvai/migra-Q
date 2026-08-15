"""API router registry."""

from fastapi import APIRouter

from backend.api.analyze import router as analyze_router
from backend.api.diagnosis import diagnosis_router
from backend.api.diagnosis_ai import diagnosis_ai_router
from backend.api.execution import router as execution_router
from backend.api.health import router as health_router
from backend.api.repair_verification import repair_verification_router
from backend.api.translation import translation_router
from backend.api.validation import validation_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analyze_router)
api_router.include_router(execution_router)
api_router.include_router(validation_router)
api_router.include_router(diagnosis_router)
api_router.include_router(translation_router)
api_router.include_router(diagnosis_ai_router)
api_router.include_router(repair_verification_router)
