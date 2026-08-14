"""Pydantic data models for laboratory schemas, manifests, and profiles."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.lab.config import GENERATOR_VERSION, SCHEMA_VERSION


class ColumnDef(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    description: str = ""


class TableSchema(BaseModel):
    table_name: str
    primary_key: list[str]
    columns: list[ColumnDef]


# Canonical entity schemas
CUSTOMER_SCHEMA = TableSchema(
    table_name="customers",
    primary_key=["customer_id"],
    columns=[
        ColumnDef(
            name="customer_id",
            data_type="string",
            nullable=False,
            description="Deterministic primary key",
        ),
        ColumnDef(name="first_name", data_type="string", nullable=False),
        ColumnDef(name="last_name", data_type="string", nullable=False),
        ColumnDef(name="date_of_birth", data_type="date", nullable=False),
        ColumnDef(name="gender", data_type="string", nullable=False),
        ColumnDef(name="email", data_type="string", nullable=False),
        ColumnDef(name="phone", data_type="string", nullable=False),
        ColumnDef(name="city", data_type="string", nullable=False),
        ColumnDef(name="state", data_type="string", nullable=False),
        ColumnDef(name="country", data_type="string", nullable=False),
        ColumnDef(
            name="customer_segment",
            data_type="string",
            nullable=False,
            description="MASS, AFFLUENT, PREMIUM",
        ),
        ColumnDef(name="customer_since", data_type="date", nullable=False),
        ColumnDef(name="annual_income", data_type="float", nullable=False),
        ColumnDef(name="credit_score", data_type="int", nullable=False),
        ColumnDef(
            name="risk_tier", data_type="string", nullable=False, description="LOW, MEDIUM, HIGH"
        ),
        ColumnDef(
            name="status",
            data_type="string",
            nullable=False,
            description="ACTIVE, INACTIVE, SUSPENDED",
        ),
        ColumnDef(name="created_at", data_type="timestamp", nullable=False),
    ],
)

ACCOUNT_SCHEMA = TableSchema(
    table_name="accounts",
    primary_key=["account_id"],
    columns=[
        ColumnDef(name="account_id", data_type="string", nullable=False),
        ColumnDef(name="customer_id", data_type="string", nullable=False),
        ColumnDef(
            name="account_type",
            data_type="string",
            nullable=False,
            description="SAVINGS, CHECKING, CREDIT, INVESTMENT",
        ),
        ColumnDef(name="opened_at", data_type="timestamp", nullable=False),
        ColumnDef(name="closed_at", data_type="timestamp", nullable=True),
        ColumnDef(name="balance", data_type="float", nullable=False),
        ColumnDef(name="credit_limit", data_type="float", nullable=False),
        ColumnDef(
            name="status", data_type="string", nullable=False, description="ACTIVE, CLOSED, FROZEN"
        ),
        ColumnDef(name="currency", data_type="string", nullable=False),
    ],
)

TRANSACTION_SCHEMA = TableSchema(
    table_name="transactions",
    primary_key=["transaction_id"],
    columns=[
        ColumnDef(name="transaction_id", data_type="string", nullable=False),
        ColumnDef(name="account_id", data_type="string", nullable=False),
        ColumnDef(name="customer_id", data_type="string", nullable=False),
        ColumnDef(name="transaction_timestamp", data_type="timestamp", nullable=False),
        ColumnDef(
            name="transaction_type",
            data_type="string",
            nullable=False,
            description="PURCHASE, REFUND, TRANSFER, WITHDRAWAL, DEPOSIT, PAYMENT, FEE",
        ),
        ColumnDef(name="amount", data_type="float", nullable=False),
        ColumnDef(name="currency", data_type="string", nullable=False),
        ColumnDef(name="merchant_category", data_type="string", nullable=True),
        ColumnDef(name="merchant_id", data_type="string", nullable=True),
        ColumnDef(
            name="channel",
            data_type="string",
            nullable=False,
            description="ONLINE, MOBILE, ATM, BRANCH, POS",
        ),
        ColumnDef(
            name="status",
            data_type="string",
            nullable=False,
            description="COMPLETED, PENDING, FAILED, REVERSED",
        ),
        ColumnDef(name="is_refund", data_type="boolean", nullable=False),
        ColumnDef(name="original_transaction_id", data_type="string", nullable=True),
    ],
)

SUPPORT_CASE_SCHEMA = TableSchema(
    table_name="support_cases",
    primary_key=["case_id"],
    columns=[
        ColumnDef(name="case_id", data_type="string", nullable=False),
        ColumnDef(name="customer_id", data_type="string", nullable=False),
        ColumnDef(name="opened_at", data_type="timestamp", nullable=False),
        ColumnDef(name="closed_at", data_type="timestamp", nullable=True),
        ColumnDef(
            name="category",
            data_type="string",
            nullable=False,
            description="PAYMENT, ACCOUNT, TRANSACTION, CARD, FRAUD, LOGIN, OTHER",
        ),
        ColumnDef(
            name="priority",
            data_type="string",
            nullable=False,
            description="LOW, MEDIUM, HIGH, CRITICAL",
        ),
        ColumnDef(
            name="status",
            data_type="string",
            nullable=False,
            description="OPEN, IN_PROGRESS, RESOLVED, CLOSED",
        ),
        ColumnDef(name="resolution_time_hours", data_type="float", nullable=True),
        ColumnDef(
            name="channel",
            data_type="string",
            nullable=False,
            description="PHONE, EMAIL, CHAT, WEB",
        ),
        ColumnDef(name="description_class", data_type="string", nullable=False),
        ColumnDef(name="satisfaction_score", data_type="int", nullable=True),
    ],
)

ALL_SCHEMAS: dict[str, TableSchema] = {
    "customers": CUSTOMER_SCHEMA,
    "accounts": ACCOUNT_SCHEMA,
    "transactions": TRANSACTION_SCHEMA,
    "support_cases": SUPPORT_CASE_SCHEMA,
}


class DatasetManifest(BaseModel):
    dataset_id: str
    generator_version: str = GENERATOR_VERSION
    schema_version: str = SCHEMA_VERSION
    seed: int
    profile: str
    generation_timestamp: str
    row_counts: dict[str, int]
    table_schemas: dict[str, TableSchema] = Field(default_factory=lambda: ALL_SCHEMAS)
    scenario_ids: list[str] = Field(default_factory=list)
    file_names: dict[str, str] = Field(default_factory=dict)
    checksums: dict[str, str] = Field(default_factory=dict)


class ColumnProfileStats(BaseModel):
    null_rate: float
    distinct_count: int
    min_val: Any = None
    max_val: Any = None
    categorical_distribution: dict[str, float] = Field(default_factory=dict)


class TableProfileStats(BaseModel):
    row_count: int
    column_stats: dict[str, ColumnProfileStats]


class DatasetProfileStats(BaseModel):
    dataset_id: str
    table_stats: dict[str, TableProfileStats]
