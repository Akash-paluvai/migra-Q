import time
from typing import Dict, Any, List
from backend.benchmark.cases.sample_cases import BENCHMARK_CASES
from backend.benchmark.metrics import BenchmarkMetricsCalculator
from backend.core.models import Dialect, MigrationRequest
from backend.execution.sandbox import ExecutionSandbox
from backend.translator.schemas import TranslationTask
from backend.translator.translator import SQLTranslator
from backend.validation.orchestrator import ValidationOrchestrator


class BenchmarkRunner:
    """Automated benchmark test suite execution engine."""

    @staticmethod
    def run_all() -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []

        for case in BENCHMARK_CASES:
            t0 = time.time()
            task = TranslationTask(
                source_sql=case["source_sql"],
                source_dialect=Dialect(case["source_dialect"]),
                target_dialect=Dialect(case["target_dialect"])
            )
            trans_res = SQLTranslator.translate(task)

            src_df, tgt_df = ExecutionSandbox.run_comparison(
                source_sql=case["source_sql"],
                target_sql=trans_res.translated_sql,
                sample_tables=case["sample_data"]
            )

            val_res = ValidationOrchestrator.run_pipeline(src_df, tgt_df, migration_id=case["case_id"])
            latency = (time.time() - t0) * 1000

            results.append({
                "case_id": case["case_id"],
                "name": case["name"],
                "passed": val_res.passed,
                "confidence_score": val_res.overall_confidence_score,
                "latency_ms": latency
            })

        metrics = BenchmarkMetricsCalculator.compute(results)
        return {
            "metrics": metrics,
            "details": results
        }


if __name__ == "__main__":
    output = BenchmarkRunner.run_all()
    print("Benchmark Execution Results:")
    print(output)
