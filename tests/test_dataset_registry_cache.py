import json
import time
from pathlib import Path
from backend.datasets.registry import DatasetRegistry, DATASETS_DIR

def test_stale_cache_invalidation():
    print("Initializing registry (v1)...")
    registry = DatasetRegistry()
    
    dataset_id = "customer_risk"
    target_dir = DATASETS_DIR / dataset_id
    manifest_file = target_dir / "manifest.json"
    
    assert target_dir.exists(), f"Dataset directory {target_dir} should exist"
    assert manifest_file.exists(), f"Manifest {manifest_file} should exist"
    
    # Read the valid spec_hash
    with open(manifest_file, "r") as f:
        data = json.load(f)
        
    original_spec_hash = data.get("spec_hash")
    assert original_spec_hash and original_spec_hash != "hash-unknown", "spec_hash should be populated"
    
    # Place a dummy file to prove the directory gets completely purged
    dummy_file = target_dir / "stale_marker.txt"
    dummy_file.write_text("I should be deleted on regeneration.")
    
    # Modify manifest to simulate that the source code changed (stale spec_hash)
    data["spec_hash"] = "stale-hash"
    with open(manifest_file, "w") as f:
        json.dump(data, f)
        
    print("Modified manifest to simulate stale cache. Re-initializing registry...")
    
    # Re-initialize registry (simulates restarting backend after code change)
    registry_v2 = DatasetRegistry()
    
    # Assertions
    assert not dummy_file.exists(), "The dataset directory was not purged! Stale cache survived."
    
    with open(manifest_file, "r") as f:
        new_data = json.load(f)
        
    assert new_data.get("spec_hash") == original_spec_hash, "The manifest was not regenerated with the correct spec_hash."
    print("SUCCESS: Stale cache was correctly invalidated and dataset was regenerated.")

if __name__ == "__main__":
    test_stale_cache_invalidation()
