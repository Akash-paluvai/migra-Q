from backend.core.models import AssuranceScorecard, ValidationPipelineResult


class AssuranceReportGenerator:
    """Generates markdown and structured JSON summary reports for stakeholders."""

    @staticmethod
    def generate_markdown_report(result: ValidationPipelineResult, scorecard: AssuranceScorecard) -> str:
        status_badge = "✅ PASSED" if scorecard.gate_passed else "❌ FAILED"
        report = f"""# Migra-Q Assurance Summary Report

**Migration ID:** `{result.migration_id}`  
**Overall Status:** {status_badge}  
**Assurance Score:** `{scorecard.assurance_score}/100`  

---

## 📊 Score Breakdown
- **Schema Alignment:** {scorecard.score_breakdown.get('schema', 0.0)}%
- **Row Equivalence:** {scorecard.score_breakdown.get('rows', 0.0)}%
- **Aggregate Verification:** {scorecard.score_breakdown.get('aggregates', 0.0)}%
- **Business Rules Compliance:** {scorecard.score_breakdown.get('business_rules', 0.0)}%
- **Edge Case Robustness:** {scorecard.score_breakdown.get('edge_cases', 0.0)}%

---

## 🔍 Validation Stage Details
- **Schema Check:** Passed = `{result.schema_check.passed}`
- **Row Count:** Source = `{result.row_check.source_row_count}`, Target = `{result.row_check.target_row_count}`, Matched = `{result.row_check.matched_row_count}`
- **Aggregates:** Differences = `{result.aggregate_check.diffs}`

---

## 💡 Recommendations
{"".join(f"- {rec}\n" for rec in scorecard.recommendations)}
"""
        return report
