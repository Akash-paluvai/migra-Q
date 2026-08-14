"""Configuration constants and dataset scale profiles for Phase 2 Synthetic Lab."""

from dataclasses import dataclass

GENERATOR_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True)
class DatasetProfile:
    name: str
    num_customers: int
    num_accounts: int
    num_transactions: int
    num_support_cases: int


PROFILES: dict[str, DatasetProfile] = {
    "test": DatasetProfile(
        name="test",
        num_customers=100,
        num_accounts=400,
        num_transactions=2000,
        num_support_cases=200,
    ),
    "dev": DatasetProfile(
        name="dev",
        num_customers=10_000,
        num_accounts=40_000,
        num_transactions=200_000,
        num_support_cases=20_000,
    ),
    "demo": DatasetProfile(
        name="demo",
        num_customers=50_000,
        num_accounts=200_000,
        num_transactions=1_000_000,
        num_support_cases=100_000,
    ),
}


def get_profile(profile_name: str) -> DatasetProfile:
    """Retrieve a dataset profile by name."""
    if profile_name not in PROFILES:
        valid = ", ".join(PROFILES.keys())
        raise ValueError(f"Unknown profile '{profile_name}'. Available profiles: {valid}")
    return PROFILES[profile_name]
