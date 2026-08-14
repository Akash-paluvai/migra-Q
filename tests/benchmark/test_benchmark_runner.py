from backend.benchmark.runner import BenchmarkRunner


def test_benchmark_runner_executes():
    results = BenchmarkRunner.run_all()
    assert "metrics" in results
    assert "total_cases" in results["metrics"]
    assert results["metrics"]["total_cases"] > 0
