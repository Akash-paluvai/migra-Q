"""Test configuration for Phase 9 assurance tests."""

import pytest

from backend.assurance.repository import MigrationAssuranceRepository


@pytest.fixture(autouse=True)
def reset_assurance_store():
    """Reset in-memory assurance store before each test."""
    MigrationAssuranceRepository.reset_memory_store()
    yield
    MigrationAssuranceRepository.reset_memory_store()
