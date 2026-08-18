"""pytest configuration setting APP_ENV="test" and PERSISTENCE_MODE="memory" for test isolation."""

import os

import pytest

from backend.core.config import settings
import backend.core.dialects  # noqa: F401 (Registers Netezza globally for tests)

os.environ["APP_ENV"] = "test"
os.environ["PERSISTENCE_MODE"] = "memory"
settings.APP_ENV = "test"
settings.PERSISTENCE_MODE = "memory"


@pytest.fixture(autouse=True)
def set_test_env():
    """Ensure test environment is active for all tests."""
    original_env = settings.APP_ENV
    original_mode = settings.PERSISTENCE_MODE
    settings.APP_ENV = "test"
    settings.PERSISTENCE_MODE = "memory"
    yield
    settings.APP_ENV = original_env
    settings.PERSISTENCE_MODE = original_mode
