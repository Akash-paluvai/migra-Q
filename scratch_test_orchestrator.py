import sys
import asyncio
import json
sys.path.append('.')

from backend.orchestrator.models import PipelineRunRequest
from backend.orchestrator.service import MigrationOrchestrator

sql = """
SELECT
    ms.region_id,
    COALESCE(sr.region_name, 'UNKNOWN') AS region_name,
    ms.sale_year,
    ms.sale_month,

    COUNT(*) AS sale_count,
    SUM(ms.revenue) AS total_revenue,
    AVG(ms.revenue) AS avg_revenue,

    SUM(SUM(ms.revenue)) OVER (
        PARTITION BY ms.region_id, ms.sale_year
    ) AS yearly_region_revenue,

    AVG(AVG(ms.revenue)) OVER (
        PARTITION BY ms.sale_year, ms.sale_month
    ) AS monthly_avg_revenue,

    LAG(SUM(ms.revenue)) OVER (
        PARTITION BY ms.region_id
        ORDER BY ms.sale_year, ms.sale_month
    ) AS previous_month_revenue,

    ROW_NUMBER() OVER (
        PARTITION BY ms.sale_year, ms.sale_month
        ORDER BY SUM(ms.revenue) DESC
    ) AS revenue_rank

FROM monthly_sales ms
LEFT JOIN sales_region sr
    ON ms.region_id = sr.region_id

WHERE ms.sale_year BETWEEN 2025 AND 2026
  AND ms.revenue IS NOT NULL

GROUP BY
    ms.region_id,
    sr.region_name,
    ms.sale_year,
    ms.sale_month

QUALIFY
    ROW_NUMBER() OVER (
        PARTITION BY ms.sale_year, ms.sale_month
        ORDER BY SUM(ms.revenue) DESC
    ) <= 3

ORDER BY
    ms.sale_year DESC,
    ms.sale_month DESC,
    revenue_rank;
"""

request = PipelineRunRequest(
    source_sql=sql,
    source_dialect="teradata",
    target_dialect="bigquery",
    dataset_id="customer_aggregation"
)

orchestrator = MigrationOrchestrator()
result = orchestrator.run(request)
if result.assurance_report:
    print("Assurance Decision:", result.assurance_report.final_status)
    print("Assurance Reason:", result.assurance_report.decision_reason)
    
if result.source_execution:
    print("Source Exec Status:", result.source_execution.status)
    if result.source_execution.error_message:
        print("Source Error:", result.source_execution.error_message)
if result.target_execution:
    print("Target Exec Status:", result.target_execution.status)
    if result.target_execution.error_message:
        print("Target Error:", result.target_execution.error_message)

