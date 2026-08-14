"""Deterministic hashing functions for queries, datasets, and files using SHA-256."""

import hashlib
from pathlib import Path
from typing import Any

from backend.execution.query_normalizer import normalize_query_sql


def hash_query(sql: str) -> str:
    """Generate SHA-256 query hash from conservatively normalized SQL text."""
    norm = normalize_query_sql(sql)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def hash_dataset_manifest(manifest_dict: dict[str, Any]) -> str:
    """Derive deterministic dataset hash from Phase 2 manifest metadata and checksums."""
    seed = manifest_dict.get("seed", 42)
    profile = manifest_dict.get("profile", "dev")
    schema_ver = manifest_dict.get("schema_version", "0.1.0")
    gen_ver = manifest_dict.get("generator_version", "0.1.0")
    checksums = manifest_dict.get("checksums", {})

    sorted_checksums = ",".join(f"{k}:{v}" for k, v in sorted(checksums.items()))
    raw_key = (
        f"seed={seed};profile={profile};schema={schema_ver};"
        f"gen={gen_ver};checksums=[{sorted_checksums}]"
    )
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


def hash_file(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file on disk."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()[:16]
