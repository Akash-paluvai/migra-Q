"""Tests for dataset reproducibility and seeding consistency."""

from backend.lab.exporters.parquet import export_to_parquet
from backend.lab.generators.dataset_builder import build_base_dataset


def test_reproducibility_same_seed(tmp_path):
    dir1 = tmp_path / "seed42_run1"
    dir2 = tmp_path / "seed42_run2"

    dfs1 = build_base_dataset(seed=42, profile_name="test")
    _, checksums1 = export_to_parquet(dfs1, dir1)

    dfs2 = build_base_dataset(seed=42, profile_name="test")
    _, checksums2 = export_to_parquet(dfs2, dir2)

    assert checksums1 == checksums2, "Same seed must produce identical SHA-256 checksums"


def test_reproducibility_different_seed(tmp_path):
    dir1 = tmp_path / "seed42"
    dir2 = tmp_path / "seed43"

    dfs1 = build_base_dataset(seed=42, profile_name="test")
    _, checksums1 = export_to_parquet(dfs1, dir1)

    dfs2 = build_base_dataset(seed=43, profile_name="test")
    _, checksums2 = export_to_parquet(dfs2, dir2)

    assert checksums1 != checksums2, "Different seeds must produce different content/checksums"
