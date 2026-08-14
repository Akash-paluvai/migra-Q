"""Customer entity generator — produces realistic synthetic customer records deterministically."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
from faker import Faker

from backend.lab.config import DatasetProfile


def generate_customers(
    profile: DatasetProfile, rng: np.random.RandomState, fake: Faker
) -> pd.DataFrame:
    """Generate synthetic customer DataFrame.

    Deterministic using controlled numpy RNG and seeded Faker.
    """
    n = profile.num_customers

    # Deterministic IDs: CUST-00000001
    customer_ids = [f"CUST-{i + 1:08d}" for i in range(n)]

    genders = rng.choice(["M", "F", "OTHER"], size=n, p=[0.49, 0.49, 0.02])
    first_names = [
        fake.first_name_female()
        if g == "F"
        else (fake.first_name_male() if g == "M" else fake.first_name())
        for g in genders
    ]
    last_names = [fake.last_name() for _ in range(n)]

    domains = ["example.com", "mail.org", "test.net", "corp.io"]
    emails = [
        f"{fn.lower()}.{ln.lower()}{i + 1}@{domains[i % len(domains)]}"
        for i, (fn, ln) in enumerate(zip(first_names, last_names))
    ]
    phones = [f"+1-555-{rng.randint(100, 999):03d}-{rng.randint(1000, 9999):04d}" for _ in range(n)]

    cities = [fake.city() for _ in range(n)]
    states = [fake.state_abbr() for _ in range(n)]
    countries = ["USA"] * n

    segments = rng.choice(["MASS", "AFFLUENT", "PREMIUM"], size=n, p=[0.70, 0.22, 0.08])

    # Income correlated with segment
    incomes = np.zeros(n)
    for i, seg in enumerate(segments):
        if seg == "MASS":
            incomes[i] = round(float(rng.uniform(25000, 75000)), 2)
        elif seg == "AFFLUENT":
            incomes[i] = round(float(rng.uniform(75000, 180000)), 2)
        else:  # PREMIUM
            incomes[i] = round(float(rng.uniform(180000, 500000)), 2)

    # Risk tier correlated with credit score
    credit_scores = rng.randint(300, 851, size=n)
    risk_tiers = []
    for score in credit_scores:
        if score >= 720:
            tier = rng.choice(["LOW", "MEDIUM"], p=[0.90, 0.10])
        elif score >= 620:
            tier = rng.choice(["LOW", "MEDIUM", "HIGH"], p=[0.20, 0.70, 0.10])
        else:
            tier = rng.choice(["MEDIUM", "HIGH"], p=[0.30, 0.70])
        risk_tiers.append(tier)

    statuses = rng.choice(["ACTIVE", "INACTIVE", "SUSPENDED"], size=n, p=[0.85, 0.10, 0.05])

    # Deterministic dates derived from epoch offset
    base_date = datetime(2015, 1, 1, tzinfo=timezone.utc).timestamp()
    end_date = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()
    since_ts = rng.uniform(base_date, end_date, size=n)
    customer_since = [pd.Timestamp(ts, unit="s", tz="UTC").strftime("%Y-%m-%d") for ts in since_ts]
    created_at = [pd.Timestamp(ts, unit="s", tz="UTC").isoformat() for ts in since_ts]

    # DOB: age 18 to 75
    dob_start = datetime(1949, 1, 1, tzinfo=timezone.utc).timestamp()
    dob_end = datetime(2006, 1, 1, tzinfo=timezone.utc).timestamp()
    dob_ts = rng.uniform(dob_start, dob_end, size=n)
    dobs = [pd.Timestamp(ts, unit="s", tz="UTC").strftime("%Y-%m-%d") for ts in dob_ts]

    df = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "first_name": first_names,
            "last_name": last_names,
            "date_of_birth": dobs,
            "gender": genders,
            "email": emails,
            "phone": phones,
            "city": cities,
            "state": states,
            "country": countries,
            "customer_segment": segments,
            "customer_since": customer_since,
            "annual_income": incomes,
            "credit_score": credit_scores,
            "risk_tier": risk_tiers,
            "status": statuses,
            "created_at": created_at,
        }
    )

    return df
