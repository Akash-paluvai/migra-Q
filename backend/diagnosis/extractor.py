"""Signal Extractor for extracting raw discrepancy signals from Phase 4 artifacts."""

from typing import Any

from backend.analyzer.models import SQLAnalysis
from backend.diagnosis.signals import RawDiscrepancySignal
from backend.validation.models import ValidationCheckStatus, ValidationReport


def _format_condition(cond: Any) -> str:
    if isinstance(cond, str):
        return cond
    if isinstance(cond, dict):
        if "condition" in cond and isinstance(cond["condition"], (dict, str)):
            return _format_condition(cond["condition"])
        op = cond.get("operator", "")
        left = cond.get("left", "")
        right = cond.get("right", "")
        if op and left and right:
            return f"{left} {op} {right}"
        if "expression" in cond:
            return str(cond["expression"])
    return str(cond)


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
                ev_dict["mismatch_count"] = chk.mismatch_count
                ev_type = ev_dict.get("type", "")
                cat = ev_dict.get("category", "")
                src_val = ev_dict.get("source_value")
                tgt_val = ev_dict.get("target_value")
                col = ev_dict.get("column")

                src_expr = _format_condition(src_val) if src_val is not None else None
                tgt_expr = _format_condition(tgt_val) if tgt_val is not None else None

                # Infer analysis path
                analysis_path = ""
                if col:
                    analysis_path = f"columns[{col}]"
                elif cat == "CASE_RULE_CHANGED":
                    analysis_path = "business_rules[0].condition"
                elif cat:
                    analysis_path = f"category[{cat}]"

                signals.append(
                    RawDiscrepancySignal(
                        source_validator=validator_name,
                        signal_type=str(ev_type),
                        analysis_path=analysis_path,
                        source_expression=src_expr,
                        target_expression=tgt_expr,
                        payload=ev_dict,
                    )
                )

        # If business rule differences exist in metadata/AST analysis, extract AST signals
        if (
            source_analysis
            and target_analysis
            and not any(s.source_validator == "BusinessRuleValidator" for s in signals)
        ):
            SignalExtractor._extract_ast_signals(source_analysis, target_analysis, signals)

        return signals

    @staticmethod
    def _extract_ast_signals(
        s: SQLAnalysis,
        t: SQLAnalysis,
        signals: list[RawDiscrepancySignal],
    ) -> None:
        """Extract structural AST signals directly from source & target SQLAnalysis."""
        # Check Business Rules & Case Expressions
        for i, sc in enumerate(s.case_expressions):
            if i < len(t.case_expressions):
                tc = t.case_expressions[i]
                for j, sw in enumerate(sc.whens):
                    if j < len(tc.whens):
                        tw = tc.whens[j]
                        if sw.condition != tw.condition:
                            target_col = sc.target_column or tc.target_column
                            if not target_col:
                                for col_ref in s.columns:
                                    col_name = (col_ref.alias or col_ref.name or "").lower()
                                    if col_name and ("risk" in col_name or "class" in col_name or col_name in ("risk_class", "risk_category", "status_class")):
                                        target_col = col_ref.alias or col_ref.name
                                        break
                            if not target_col:
                                for col_ref in reversed(s.columns):
                                    col_name = (col_ref.alias or col_ref.name or "").lower()
                                    if col_name and col_name not in ("customer_id", "customer_segment", "account_id", "amount", "status"):
                                        target_col = col_ref.alias or col_ref.name
                                        break

                            is_op_inc = (">" in sw.condition and ">=" in tw.condition) or (">=" in sw.condition and ">" in tw.condition) or ("<" in sw.condition and "<=" in tw.condition) or ("<=" in sw.condition and "<" in tw.condition)
                            signals.append(
                                RawDiscrepancySignal(
                                    source_validator="AST_ANALYZER",
                                    signal_type="OPERATOR_INCLUSION" if is_op_inc else "CASE_CONDITION_DIFF",
                                    analysis_path=f"columns[{target_col}]" if target_col else f"case_expressions[{i}].whens[{j}]",
                                    source_expression=sw.condition,
                                    target_expression=tw.condition,
                                    payload={
                                        "case_id": sc.id,
                                        "column": target_col,
                                        "source_result": sw.result,
                                        "target_result": tw.result,
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
