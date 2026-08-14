"""Tests for support case generator."""

import numpy as np
from faker import Faker

from backend.lab.config import get_profile
from backend.lab.generators.customers import generate_customers
from backend.lab.generators.support_cases import generate_support_cases


def test_support_cases_generator():
    profile = get_profile("dev")
    rng = np.random.RandomState(42)
    fake = Faker()
    fake.seed_instance(42)

    cust_df = generate_customers(profile, rng, fake)
    case_df = generate_support_cases(cust_df, profile, rng, fake)

    assert len(case_df) == 20000
    assert case_df["case_id"].is_unique

    cust_set = set(cust_df["customer_id"])
    case_cust_set = set(case_df["customer_id"])
    assert case_cust_set.issubset(cust_set)
