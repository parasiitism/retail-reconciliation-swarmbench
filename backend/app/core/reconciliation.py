import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.app.connectors.csv_connector import CsvConnector
from backend.app.core.catalog import load_product_catalog
from backend.app.core.config import PRODUCT_CATALOG_PATH, REPORTS_DIR, SAMPLE_RETAIL_DIR
from backend.app.core.models import (
    AuditEvent,
    CanonicalTransaction,
    CategorySummary,
    MultiSourceReconciliationReport,
    ReconciliationReport,
)
from backend.app.core.schema_mapping import get_value
from backend.app.core.report_writer import write_json_report

REFUND_TYPES = {"refund", "return", "returned"}


def to_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def normalize_row(
    row: dict[str, str],
    source_id: str,
    product_catalog: dict[str, str] | None = None,
) -> CanonicalTransaction:
    product_catalog = product_catalog or {}

    quantity = int(get_value(row, "quantity"))
    unit_price = Decimal(get_value(row, "unit_price"))
    raw_type = get_value(row, "transaction_type").strip().lower()
    sku = get_value(row, "sku")

    transaction_type = "refund" if quantity < 0 or raw_type in REFUND_TYPES else "sale"
    amount = to_money(abs(Decimal(quantity)) * unit_price)
    category = product_catalog.get(sku, "unknown")

    return CanonicalTransaction(
        transaction_id=get_value(row, "transaction_id"),
        source_id=source_id,
        transaction_date=get_value(row, "transaction_date"),
        sku=sku,
        category=category,
        quantity=quantity,
        unit_price=unit_price,
        transaction_type=transaction_type,
        amount=amount,
    )


def reconcile_transactions(
    source_id: str,
    transactions: list[CanonicalTransaction],
    raw_row_count: int,
) -> ReconciliationReport:
    gross_sales = Decimal("0.00")
    refunds = Decimal("0.00")
    sale_count = 0
    refund_count = 0

    for transaction in transactions:
        if transaction.transaction_type == "refund":
            refunds += transaction.amount
            refund_count += 1
        else:
            gross_sales += transaction.amount
            sale_count += 1

    return ReconciliationReport(
        source_id=source_id,
        raw_row_count=raw_row_count,
        transaction_count=len(transactions),
        sale_count=sale_count,
        refund_count=refund_count,
        gross_sales=to_money(gross_sales),
        refunds=to_money(refunds),
        net_revenue=to_money(gross_sales - refunds),
    )

def load_transactions_from_csv(
    csv_path: Path,
    source_id: str,
    product_catalog: dict[str, str] | None = None,
) -> tuple[int, list[CanonicalTransaction]]:
    connector = CsvConnector(csv_path)
    rows = connector.fetch_rows()
    transactions = [
        normalize_row(row, source_id=source_id, product_catalog=product_catalog)
        for row in rows
    ]
    return len(rows), transactions


def reconcile_csv(
    csv_path: Path,
    source_id: str,
    product_catalog: dict[str, str] | None = None,
) -> ReconciliationReport:
    raw_row_count, transactions = load_transactions_from_csv(
        csv_path=csv_path,
        source_id=source_id,
        product_catalog=product_catalog,
    )

    return reconcile_transactions(
        source_id=source_id,
        transactions=transactions,
        raw_row_count=raw_row_count,
    )


def build_category_totals(
    transactions: list[CanonicalTransaction],
) -> dict[str, CategorySummary]:
    category_buckets: dict[str, dict[str, Decimal | int]] = {}

    for transaction in transactions:
        category = transaction.category

        if category not in category_buckets:
            category_buckets[category] = {
                "transaction_count": 0,
                "sale_count": 0,
                "refund_count": 0,
                "gross_sales": Decimal("0.00"),
                "refunds": Decimal("0.00"),
            }

        bucket = category_buckets[category]
        bucket["transaction_count"] += 1

        if transaction.transaction_type == "refund":
            bucket["refund_count"] += 1
            bucket["refunds"] += transaction.amount
        else:
            bucket["sale_count"] += 1
            bucket["gross_sales"] += transaction.amount

    category_totals: dict[str, CategorySummary] = {}

    for category, bucket in category_buckets.items():
        gross_sales = bucket["gross_sales"]
        refunds = bucket["refunds"]

        category_totals[category] = CategorySummary(
            transaction_count=int(bucket["transaction_count"]),
            sale_count=int(bucket["sale_count"]),
            refund_count=int(bucket["refund_count"]),
            gross_sales=to_money(gross_sales),
            refunds=to_money(refunds),
            net_revenue=to_money(gross_sales - refunds),
        )

    return category_totals


def find_unmapped_skus(transactions: list[CanonicalTransaction]) -> list[str]:
    return sorted(
        {
            transaction.sku
            for transaction in transactions
            if transaction.category == "unknown"
        }
    )


def build_unmapped_sku_audit_events(
    transactions: list[CanonicalTransaction],
) -> list[AuditEvent]:
    audit_events: list[AuditEvent] = []
    seen_unmapped_skus: set[tuple[str, str]] = set()

    for transaction in transactions:
        if transaction.category != "unknown":
            continue

        key = (transaction.source_id, transaction.sku)
        if key in seen_unmapped_skus:
            continue

        seen_unmapped_skus.add(key)

        audit_events.append(
            AuditEvent(
                event_type="unmapped_sku",
                source_id=transaction.source_id,
                transaction_id=transaction.transaction_id,
                sku=transaction.sku,
                message=(
                    f"SKU {transaction.sku} from source {transaction.source_id}"
                    " was not found in the product catalog."
                ),
                severity="warning",
            )
        )

    return audit_events


def reconcile_many_csvs(
    source_paths: dict[str, Path],
    product_catalog: dict[str, str] | None = None,
) -> MultiSourceReconciliationReport:
    source_reports: dict[str, ReconciliationReport] = {}
    deduped_transactions: list[CanonicalTransaction] = []
    seen_transaction_ids: set[str] = set()
    seen_transaction_sources: dict[str, str] = {}
    duplicate_transaction_ids: list[str] = []
    audit_events: list[AuditEvent] = []
    total_raw_row_count = 0

    for source_id, csv_path in source_paths.items():
        raw_row_count, transactions = load_transactions_from_csv(
            csv_path=csv_path,
            source_id=source_id,
            product_catalog=product_catalog,
        )
        total_raw_row_count += raw_row_count

        source_reports[source_id] = reconcile_transactions(
            source_id=source_id,
            transactions=transactions,
            raw_row_count=raw_row_count,
        )

        for transaction in transactions:
            if transaction.transaction_id in seen_transaction_ids:
                original_source = seen_transaction_sources[transaction.transaction_id]
                duplicate_transaction_ids.append(transaction.transaction_id)

                audit_events.append(
                    AuditEvent(
                        event_type="duplicate_skipped",
                        source_id=source_id,
                        transaction_id=transaction.transaction_id,
                        sku=transaction.sku,
                        message=(
                            f"Transaction {transaction.transaction_id} from source "
                            f"{source_id} was skipped because it already appeared "
                            f"in source {original_source}."
                        ),
                        severity="warning",
                    )
                )
                continue

            seen_transaction_ids.add(transaction.transaction_id)
            seen_transaction_sources[transaction.transaction_id] = source_id
            deduped_transactions.append(transaction)

    audit_events.extend(build_unmapped_sku_audit_events(deduped_transactions))

    global_report = reconcile_transactions(
        source_id="global",
        transactions=deduped_transactions,
        raw_row_count=total_raw_row_count,
    )

    return MultiSourceReconciliationReport(
        source_count=len(source_reports),
        raw_row_count=global_report.raw_row_count,
        transaction_count=global_report.transaction_count,
        sale_count=global_report.sale_count,
        refund_count=global_report.refund_count,
        gross_sales=global_report.gross_sales,
        refunds=global_report.refunds,
        net_revenue=global_report.net_revenue,
        duplicate_transaction_ids=duplicate_transaction_ids,
        unmapped_skus=find_unmapped_skus(deduped_transactions),
        audit_events=audit_events,
        category_totals=build_category_totals(deduped_transactions),
        source_reports=source_reports,
    )


def report_to_json(report: ReconciliationReport | MultiSourceReconciliationReport) -> str:
    if hasattr(report, "model_dump_json"):
        return report.model_dump_json(indent=2)
    return report.json(indent=2)


if __name__ == "__main__":
    product_catalog = load_product_catalog(PRODUCT_CATALOG_PATH)

    source_paths = {
        "atlanta": SAMPLE_RETAIL_DIR / "atlanta.csv",
        "boston": SAMPLE_RETAIL_DIR / "boston.csv",
    }
    report = reconcile_many_csvs(
        source_paths=source_paths,
        product_catalog=product_catalog,
    )
    print(report_to_json(report))
    output_path = REPORTS_DIR / "latest_report.json"
    saved_path = write_json_report(report=report, output_path=output_path)
    print(f"\nReport saved to: {saved_path}")
