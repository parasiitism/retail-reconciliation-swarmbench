from decimal import Decimal

from backend.app.core.models import (
    MultiSourceReconciliationReport,
    ValidationIssue,
    ValidationResult,
)


def validate_report(report: MultiSourceReconciliationReport) -> ValidationResult:
    issues: list[ValidationIssue] = []

    expected_net_revenue = report.gross_sales - report.refunds

    if expected_net_revenue != report.net_revenue:
        issues.append(
            ValidationIssue(
                code="NET_REVENUE_MISMATCH",
                message="gross_sales - refunds does not equal net_revenue",
                severity="error",
            )
        )

    if report.raw_row_count < report.transaction_count:
        issues.append(
            ValidationIssue(
                code="ROW_COUNT_INVALID",
                message="raw_row_count cannot be smaller than transaction_count",
                severity="error",
            )
        )

    category_gross_sales = sum(
        (category.gross_sales for category in report.category_totals.values()),
        Decimal("0.00"),
    )

    category_refunds = sum(
        (category.refunds for category in report.category_totals.values()),
        Decimal("0.00"),
    )

    category_net_revenue = sum(
        (category.net_revenue for category in report.category_totals.values()),
        Decimal("0.00"),
    )

    if category_gross_sales != report.gross_sales:
        issues.append(
            ValidationIssue(
                code="CATEGORY_GROSS_MISMATCH",
                message="category gross sales total does not match global gross sales",
                severity="error",
            )
        )

    if category_refunds != report.refunds:
        issues.append(
            ValidationIssue(
                code="CATEGORY_REFUND_MISMATCH",
                message="category refund total does not match global refunds",
                severity="error",
            )
        )

    if category_net_revenue != report.net_revenue:
        issues.append(
            ValidationIssue(
                code="CATEGORY_NET_REVENUE_MISMATCH",
                message="category net revenue total does not match global net revenue",
                severity="error",
            )
        )

    return ValidationResult(
        is_valid=not any(issue.severity == "error" for issue in issues),
        issue_count=len(issues),
        issues=issues,
    )
