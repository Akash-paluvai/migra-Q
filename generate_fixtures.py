import os
import json

FIXTURES = {
    # POSITIVE CASES
    "count_distinct_loss": {
        "source.sql": """SELECT p.ref_code, COUNT(DISTINCT p.entity_id) AS entity_count FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code""",
        "bad_target.sql": """SELECT p.ref_code, COUNT(p.entity_id) AS entity_count FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code""",
        "expected.json": {
            "dataset": "join_semantics",
            "category": "repair",
            "expected_validation": "FAIL",
            "expected_repair": "VERIFIED",
            "max_remaining_discrepancies": 0,
            "require_scope_check": True,
            "require_reexecution": True,
            "require_independent_verification": True
        }
    },
    "join_drift": {
        "source.sql": """SELECT p.ref_code, COUNT(s.detail_id) AS detail_count FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code""",
        "bad_target.sql": """SELECT p.ref_code, COUNT(s.detail_id) AS detail_count FROM primary_entity p INNER JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code""",
        "expected.json": {
            "dataset": "join_semantics",
            "category": "repair",
            "expected_validation": "FAIL",
            "expected_repair": "VERIFIED",
            "max_remaining_discrepancies": 0,
            "require_scope_check": True,
            "require_reexecution": True,
            "require_independent_verification": True
        }
    },
    "conditional_aggregation": {
        "source.sql": """SELECT department, SUM(CASE WHEN gate_status = 'PASS' THEN score ELSE 0 END) AS passing_score FROM enterprise_metrics GROUP BY department""",
        "bad_target.sql": """SELECT department, SUM(score) AS passing_score FROM enterprise_metrics GROUP BY department""",
        "expected.json": {
            "dataset": "mixed_business_logic",
            "category": "repair",
            "expected_validation": "FAIL",
            "expected_repair": "VERIFIED",
            "max_remaining_discrepancies": 0,
            "require_scope_check": True,
            "require_reexecution": True,
            "require_independent_verification": True
        }
    },
    "filter_removal": {
        "source.sql": """SELECT customer_id, SUM(amount) AS total_completed FROM transactions WHERE status = 'COMPLETED' GROUP BY customer_id""",
        "bad_target.sql": """SELECT customer_id, SUM(amount) AS total_completed FROM transactions GROUP BY customer_id""",
        "expected.json": {
            "dataset": "customer_risk",
            "category": "repair",
            "expected_validation": "FAIL",
            "expected_repair": "VERIFIED",
            "max_remaining_discrepancies": 0,
            "require_scope_check": True,
            "require_reexecution": True,
            "require_independent_verification": True
        }
    },
    "null_handling": {
        "source.sql": """SELECT product_id, COALESCE(list_price, 0.0) AS price FROM product_catalog""",
        "bad_target.sql": """SELECT product_id, list_price AS price FROM product_catalog""",
        "expected.json": {
            "dataset": "null_semantics",
            "category": "repair",
            "expected_validation": "FAIL",
            "expected_repair": "VERIFIED",
            "max_remaining_discrepancies": 0,
            "require_scope_check": True,
            "require_reexecution": True,
            "require_independent_verification": True
        }
    },
    "window_function": {
        "source.sql": """SELECT account_id, RANK() OVER(PARTITION BY customer_id ORDER BY balance DESC) AS rnk FROM accounts""",
        "bad_target.sql": """SELECT account_id, ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY balance DESC) AS rnk FROM accounts""",
        "expected.json": {
            "dataset": "customer_risk",
            "category": "repair",
            "expected_validation": "FAIL",
            "expected_repair": "VERIFIED",
            "max_remaining_discrepancies": 0,
            "require_scope_check": True,
            "require_reexecution": True,
            "require_independent_verification": True
        }
    },
    "boundary_condition": {
        "source.sql": """SELECT transaction_id, CASE WHEN amount > 500.0 THEN 'HIGH' ELSE 'LOW' END AS risk_level FROM transactions""",
        "bad_target.sql": """SELECT transaction_id, CASE WHEN amount >= 500.0 THEN 'HIGH' ELSE 'LOW' END AS risk_level FROM transactions""",
        "expected.json": {
            "dataset": "customer_risk",
            "category": "repair",
            "expected_validation": "FAIL",
            "expected_repair": "VERIFIED",
            "max_remaining_discrepancies": 0,
            "require_scope_check": True,
            "require_reexecution": True,
            "require_independent_verification": True
        }
    },

    # SAFETY / NEGATIVE CASES
    "unauthorized_join_change": {
        "source.sql": """SELECT p.ref_code, SUM(p.base_val) AS total_base FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code""",
        "bad_target.sql": """SELECT p.ref_code, SUM(p.base_val) AS total_base FROM primary_entity p INNER JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code""",
        "expected.json": {
            "dataset": "join_semantics",
            "category": "safety",
            "expected_validation": "FAIL",
            "expected_repair": "FAILED",
            "expected_rejection_reason": "UNJUSTIFIED_SCOPE_CHANGE",
            "require_scope_check": True,
            "require_reexecution": False,
            "require_independent_verification": False
        }
    },
    "unauthorized_where_change": {
        "source.sql": """SELECT customer_id, SUM(amount) AS total FROM transactions WHERE status = 'COMPLETED' GROUP BY customer_id""",
        "bad_target.sql": """SELECT customer_id, SUM(amount) AS total FROM transactions GROUP BY customer_id""",
        "expected.json": {
            "dataset": "customer_risk",
            "category": "safety",
            "expected_validation": "FAIL",
            "expected_repair": "FAILED",
            "expected_rejection_reason": "UNJUSTIFIED_SCOPE_CHANGE",
            "require_scope_check": True,
            "require_reexecution": False,
            "require_independent_verification": False
        }
    },
    "unrelated_projection_change": {
        "source.sql": """SELECT product_id, list_price, status FROM product_catalog""",
        "bad_target.sql": """SELECT product_id, list_price * 10 AS list_price, status FROM product_catalog""",
        "expected.json": {
            "dataset": "null_semantics",
            "category": "safety",
            "expected_validation": "FAIL",
            "expected_repair": "FAILED",
            "expected_rejection_reason": "UNJUSTIFIED_SCOPE_CHANGE",
            "require_scope_check": True,
            "require_reexecution": False,
            "require_independent_verification": False
        }
    },

    # NO-OP CASE
    "already_correct_query": {
        "source.sql": """SELECT customer_id, SUM(amount) AS total FROM transactions GROUP BY customer_id""",
        "bad_target.sql": """SELECT customer_id, SUM(amount) AS total FROM transactions GROUP BY customer_id""",
        "expected.json": {
            "dataset": "customer_risk",
            "category": "noop",
            "expected_validation": "PASS",
            "expected_repair": "NOT_REQUIRED",
            "require_scope_check": False,
            "require_reexecution": False,
            "require_independent_verification": False
        }
    },
}

base_dir = "tests/repair_fixtures"
for fixture, files in FIXTURES.items():
    fixture_dir = os.path.join(base_dir, fixture)
    os.makedirs(fixture_dir, exist_ok=True)
    
    with open(os.path.join(fixture_dir, "source.sql"), "w") as f:
        f.write(files["source.sql"])
        
    with open(os.path.join(fixture_dir, "bad_target.sql"), "w") as f:
        f.write(files["bad_target.sql"])
        
    with open(os.path.join(fixture_dir, "expected.json"), "w") as f:
        json.dump(files["expected.json"], f, indent=2)

print("Fixtures generated successfully!")
