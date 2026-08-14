from typing import List, Dict, Any


class BenchmarkMetricsCalculator:
    """Calculates benchmark metrics: accuracy rate, avg latency, repair success rate."""

    @staticmethod
    def compute(results: List[Dict[str, Any]]) -> Dict[str, float]:
        if not results:
            return {"total": 0, "accuracy_rate": 0.0, "avg_latency_ms": 0.0}

        total = len(results)
        passed = sum(1 for r in results if r.get("passed", False))
        total_time = sum(r.get("latency_ms", 0.0) for r in results)

        return {
            "total_cases": total,
            "passed_cases": passed,
            "accuracy_rate": round(passed / total, 4),
            "avg_latency_ms": round(total_time / total, 2)
        }
