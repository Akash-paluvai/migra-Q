"""Type normalization and compatibility mapping across database engines."""

TYPE_EQUIVALENCE_GROUPS = {
    "STRING": {"VARCHAR", "STRING", "TEXT", "CHAR", "NVARCHAR"},
    "INTEGER": {"INT", "BIGINT", "INTEGER", "SMALLINT", "TINYINT", "INT64", "INT32"},
    "FLOAT": {
        "FLOAT",
        "DOUBLE",
        "REAL",
        "DECIMAL",
        "NUMERIC",
        "FLOAT8",
        "FLOAT4",
        "DOUBLE PRECISION",
    },
    "BOOLEAN": {"BOOLEAN", "BOOL"},
    "DATE": {"DATE"},
    "TIMESTAMP": {"TIMESTAMP", "DATETIME", "TIMESTAMPTZ", "TIMESTAMP WITH TIME ZONE"},
}


def normalize_type_string(raw_type: str) -> str:
    """Normalize raw SQL type string to canonical type name (e.g. VARCHAR -> STRING)."""
    if not raw_type:
        return "UNKNOWN"

    clean_type = raw_type.upper().split("(")[0].strip()

    for canonical, synonyms in TYPE_EQUIVALENCE_GROUPS.items():
        if clean_type in synonyms:
            return canonical

    return clean_type


def are_types_compatible(type1: str, type2: str) -> bool:
    """Determine whether two raw type strings are semantically compatible."""
    norm1 = normalize_type_string(type1)
    norm2 = normalize_type_string(type2)
    return norm1 == norm2
