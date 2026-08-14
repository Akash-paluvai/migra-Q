"""
API Endpoints Router Package.
"""
from fastapi import APIRouter
from backend.api.migrations import router as migrations_router
from backend.api.validation import router as validation_router
from backend.api.repairs import router as repairs_router
from backend.api.reports import router as reports_router

api_router = APIRouter()
api_router.include_router(migrations_router, prefix="/migrations", tags=["Migrations"])
api_router.include_router(validation_router, prefix="/validation", tags=["Validation"])
api_router.include_router(repairs_router, prefix="/repairs", tags=["Repairs"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])

__all__ = ["api_router"]
