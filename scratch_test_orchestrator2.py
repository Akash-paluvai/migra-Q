import sys
sys.path.append('.')

from backend.datasets.registry import DatasetRegistry
registry = DatasetRegistry()
for ds_id in registry.list_datasets():
    print(f"Dataset {ds_id}:")
    for t in registry.resolve_schema(ds_id):
        print(f" - {t.table_name}")
