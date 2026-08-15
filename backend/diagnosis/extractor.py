"""Signal Extractor for extracting raw discrepancy signals from Phase 4 artifacts."""

from backend.analyzer.models import SQLAnalysis
from backend.diagnosis.signals import RawDiscrepancySignal
from backend.validation.models import ValidationCheckStatus, ValidationReport


class SignalExtractor:
    """Extracts raw discrepancy signals from ValidationReport and SQLAnalysis structures."""

    @staticmethod
    def extract_signals(
        report: ValidationReport,
        source_analysis: SQLAnalysis | None = None,
        target_analysis: SQLAnalysis | None = None,
    ) -> list[RawDiscrepancySignal]:
        """Extract typed RawDiscrepancySignal objects from report checks and evidence."""
        signals: list[RawDiscrepancySignal] = []

        for chk in report.checks:
            if chk.status in (ValidationCheckStatus.PASS, ValidationCheckStatus.SKIPPED):
                continue

            validator_name = chk.check_name

            # Process evidence items inside check
            for ev in chk.evidence:
                ev_dict = ev.model_dump()
                ev_type = ev_dict.get("type", "")
                cat = ev_dict.get("category", "")
                src_val = ev_dict.get("source_value")
                tgt_val = ev_dict.get("target_value")
                col = ev_dict.get("column")

                # Infer analysis path
                analysis_path = ""
                if col:
                    analysis_path = f"columns[{col}]"
                elif cat:
                    analysis_path = f"category[{cat}]"

                signals.append(
                    RawDiscrepancySignal(
                        source_validator=validator_name,
                        signal_type=str(ev_type),
                        analysis_path=analysis_path,
                        source_expression=str(src_val) if src_val is not None else None,
                        target_expression=str(tgt_val) if tgt_val is not None else None,
                        payload=ev_dict,
                    )
                )

        # If business rule differences exist in metadata/AST analysis, extract AST signals
        if source_analysis and target_analysis:
            SignalExtractor._extract_ast_signals(source_analysis, target_analysis, signals)

        return signals

    @staticmethod
    def _extract_ast_signals(
        s: SQLAnalysis,
        t: SQLAnalysis,
        signals: list[RawDiscrepancySignal],
    ) -> None:
        """Extract structural AST signals directly from source & target SQLAnalysis."""
        # Check Business Rules
        for i, sr in enumerate(s.business_rules):
            if i < len(t.business_rules):
                tr = t.business_rules[i]
                if sr.condition != tr.condition or sr.outputs != tr.outputs:
                    signals.append(
                        RawDiscrepancySignal(
                            source_validator="AST_ANALYZER",
                            signal_type="BUSINESS_RULE_DIFF",
                            analysis_path=f"business_rules[{i}].condition",
                            source_expression=sr.condition,
                            target_expression=tr.condition,
                            payload={
                                "rule_id": sr.id,
                                "source_outputs": sr.outputs,
                                "target_outputs": tr.outputs,
                            },
                        )
                    )

        # Check Filters
        for i, sf in enumerate(s.filters):
            if i < len(t.filters):
                tf = t.filters[i]
                if sf.expression != tf.expression:
                    signals.append(
                        RawDiscrepancySignal(
                            source_validator="AST_ANALYZER",
                            signal_type="FILTER_DIFF",
                            analysis_path=f"filters[{i}].expression",
                            source_expression=sf.expression,
                            target_expression=tf.expression,
                            payload={"scope": sf.scope},
                        )
                    )

        # Check Joins
        for i, sj in enumerate(s.joins):
            if i < len(t.joins):
                tj = t.joins[i]
                if sj.join_type != tj.join_type or sj.condition != tj.condition:
                    signals.append(
                        RawDiscrepancySignal(
                            source_validator="AST_ANALYZER",
                            signal_type="JOIN_DIFF",
                            analysis_path=f"joins[{i}]",
                            source_expression=f"{sj.join_type} JOIN ON {sj.condition}",
                            target_expression=f"{tj.join_type} JOIN ON {tj.condition}",
                            payload={
                                "left": sj.left,
                                "right": sj.right,
                                "source_type": sj.join_type,
                                "target_type": tj.join_type,
                            },
                        )
                    )

        # Check Aggregations
        for i, sa in enumerate(s.aggregations):
            if i < len(t.aggregations):
                ta = t.aggregations[i]
                s_dist = "DISTINCT " if sa.distinct else ""
                t_dist = "DISTINCT " if ta.distinct else ""
                if (
                    sa.function != ta.function
                    or sa.expression != ta.expression
                    or sa.distinct != ta.distinct
                ):
                    signals.append(
                        RawDiscrepancySignal(
                            source_validator="AST_ANALYZER",
                            signal_type="AGGREGATION_DIFF",
                            analysis_path=f"aggregations[{i}]",
                            source_expression=f"{sa.function}({s_dist}{sa.expression})",
                            target_expression=f"{ta.function}({t_dist}{ta.expression})",
                            payload={
                                "source_distinct": sa.distinct,
                                "target_distinct": ta.distinct,
                            },
                        )
                    )
