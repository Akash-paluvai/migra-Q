"""Tests for customer generator."""

import numpy as np
from faker import Faker

from backend.lab.config import get_profile
from backend.lab.generators.customers import generate_customers


def test_customer_generator_columns_and_counts():
    profile = get_profile("dev")
    rng = np.random.RandomState(42)
    fake = Faker()
    fake.seed_instance(42)

    df = generate_customers(profile, rng, fake)

    assert len(df) == 10000
    assert df["customer_id"].is_unique
    assert set(df["customer_segment"].unique()).issubset({"MASS", "AFFLUENT", "PREMIUM"})
    assert set(df["risk_tier"].unique()).issubset({"LOW", "MEDIUM", "HIGH"})
    assert set(df["status"].unique()).issubset({"ACTIVE", "INACTIVE", "SUSPENDED"})
    assert (df["credit_score"] >= 300).all() and (df["credit_score"] <= 850).all()
