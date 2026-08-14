"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import api_router
from backend.core.config import settings
from backend.core.logging import get_logger, setup_logging
from backend.db.duckdb_check import check_duckdb

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    logger.info("Starting %s (env=%s)", settings.APP_NAME, settings.APP_ENV)
    check_duckdb()
