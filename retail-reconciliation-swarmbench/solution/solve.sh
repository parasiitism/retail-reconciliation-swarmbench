#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INPUT_DIR="${INPUT_DIR:-/environment/input_artifacts}"
if [ ! -d "$INPUT_DIR" ]; then
  INPUT_DIR="$TASK_ROOT/environment/input_artifacts"
fi

DEFAULT_OUTPUT="/workspace/report.json"
if [ ! -d "/workspace" ]; then
  DEFAULT_OUTPUT="$TASK_ROOT/report.json"
fi
OUTPUT_PATH="${1:-${REPORT_PATH:-$DEFAULT_OUTPUT}}"
mkdir -p "$(dirname "$OUTPUT_PATH")"

python - "$INPUT_DIR" "$OUTPUT_PATH" <<'PY'
import csv
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

INPUT_DIR = Path(sys.argv[1])
OUTPUT_PATH = Path(sys.argv[2])

STORE_ORDER = [
    "atlanta",
    "boston",
    "chicago",
    "denver",
    "el_paso",
    "fresno",
    "grand_rapids",
    "houston",
    "indianapolis",
    "jackson",
]
CATEGORY_ORDER = [
    "beverages",
    "pantry",
    "household",
    "personal_care",
    "electronics",
    "unknown",
]
ALIASES = {
    "transaction_id": ["transaction_id", "txn_id", "id", "order_no", "receipt", "transaction", "sale_id", "tid", "transaction_ref"],
    "date": ["date", "txn_date", "sold_at", "day", "date_sold", "business_date", "when", "store_day"],
    "sku": ["sku", "item_code", "product", "sku_code", "product_sku", "item", "upc", "product_id"],
    "quantity": ["quantity", "units", "qty", "count", "quantity_sold", "qty_sold", "number", "item_qty"],
    "unit_price": ["unit_price", "price_each", "unit_cost", "unit_amount", "sale_price", "price", "each", "amount_per_unit"],
    "transaction_type": ["transaction_type", "kind", "status", "action", "type", "mode", "operation", "txn_kind", "event"],
}
SALE_TYPES = {"sale", "order", "sold"}
REFUND_TYPES = {"refund", "return", "returned"}


def first(row, key):
    for name in ALIASES[key]:
        if name in row:
            return row[name]
    raise KeyError(f"missing {key} in columns {sorted(row)}")


def money(value):
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def read_catalog():
    with (INPUT_DIR / "product_catalog.csv").open("r", encoding="utf-8", newline="") as handle:
        return {row["sku"]: row["category"] for row in csv.DictReader(handle)}


def blank_store():
    return {
        "raw_row_count": 0,
        "deduped_transaction_count": 0,
        "sale_count": 0,
        "refund_count": 0,
        "gross_sales": Decimal("0"),
        "refunds": Decimal("0"),
        "net_revenue": Decimal("0"),
        "units_sold": 0,
        "units_refunded": 0,
        "unmapped_skus": set(),
    }


def blank_category():
    return {
        "transaction_count": 0,
        "gross_sales": Decimal("0"),
        "refunds": Decimal("0"),
        "net_revenue": Decimal("0"),
        "units_sold": 0,
        "units_refunded": 0,
    }


def load_store_rows(store, catalog):
    path = INPUT_DIR / f"{store}.csv"
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row_index, row in enumerate(csv.DictReader(handle)):
            quantity = Decimal(first(row, "quantity"))
            unit_price = Decimal(first(row, "unit_price"))
            transaction_label = first(row, "transaction_type").strip().lower()
            transaction_type = "refund" if quantity < 0 or transaction_label in REFUND_TYPES else "sale"
            sku = first(row, "sku")
            rows.append(
                {
                    "transaction_id": first(row, "transaction_id"),
                    "store": store,
                    "row_index": row_index,
                    "date": first(row, "date"),
                    "sku": sku,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "transaction_type": transaction_type,
                    "category": catalog.get(sku, "unknown"),
                    "amount": abs(quantity) * unit_price,
                }
            )
    return rows


def apply_transaction(store_stats, category_stats, tx):
    store = store_stats[tx["store"]]
    category = category_stats[tx["category"]]
    amount = tx["amount"]
    units = int(abs(tx["quantity"]))

    store["deduped_transaction_count"] += 1
    category["transaction_count"] += 1

    if tx["category"] == "unknown":
        store["unmapped_skus"].add(tx["sku"])

    if tx["transaction_type"] == "refund":
        store["refund_count"] += 1
        store["refunds"] += amount
        store["net_revenue"] -= amount
        store["units_refunded"] += units
        category["refunds"] += amount
        category["net_revenue"] -= amount
        category["units_refunded"] += units
    else:
        store["sale_count"] += 1
        store["gross_sales"] += amount
        store["net_revenue"] += amount
        store["units_sold"] += units
        category["gross_sales"] += amount
        category["net_revenue"] += amount
        category["units_sold"] += units


def serialise_store(stats):
    return {
        "raw_row_count": stats["raw_row_count"],
        "deduped_transaction_count": stats["deduped_transaction_count"],
        "sale_count": stats["sale_count"],
        "refund_count": stats["refund_count"],
        "gross_sales": money(stats["gross_sales"]),
        "refunds": money(stats["refunds"]),
        "net_revenue": money(stats["net_revenue"]),
        "units_sold": stats["units_sold"],
        "units_refunded": stats["units_refunded"],
        "unmapped_skus": sorted(stats["unmapped_skus"]),
    }


def serialise_category(stats):
    return {
        "transaction_count": stats["transaction_count"],
        "gross_sales": money(stats["gross_sales"]),
        "refunds": money(stats["refunds"]),
        "net_revenue": money(stats["net_revenue"]),
        "units_sold": stats["units_sold"],
        "units_refunded": stats["units_refunded"],
    }


def main():
    catalog = read_catalog()
    store_stats = {store: blank_store() for store in STORE_ORDER}
    category_stats = {category: blank_category() for category in CATEGORY_ORDER}
    seen = set()
    duplicate_ids = set()

    for store in STORE_ORDER:
        rows = load_store_rows(store, catalog)
        store_stats[store]["raw_row_count"] = len(rows)
        for tx in rows:
            if tx["transaction_id"] in seen:
                duplicate_ids.add(tx["transaction_id"])
                continue
            seen.add(tx["transaction_id"])
            apply_transaction(store_stats, category_stats, tx)

    stores = {store: serialise_store(store_stats[store]) for store in STORE_ORDER}
    categories = {category: serialise_category(category_stats[category]) for category in CATEGORY_ORDER}
    totals = {
        "raw_row_count": sum(store["raw_row_count"] for store in stores.values()),
        "deduped_transaction_count": sum(store["deduped_transaction_count"] for store in stores.values()),
        "sale_count": sum(store["sale_count"] for store in stores.values()),
        "refund_count": sum(store["refund_count"] for store in stores.values()),
        "gross_sales": money(sum((store_stats[store]["gross_sales"] for store in STORE_ORDER), Decimal("0"))),
        "refunds": money(sum((store_stats[store]["refunds"] for store in STORE_ORDER), Decimal("0"))),
        "net_revenue": money(sum((store_stats[store]["net_revenue"] for store in STORE_ORDER), Decimal("0"))),
        "units_sold": sum(store["units_sold"] for store in stores.values()),
        "units_refunded": sum(store["units_refunded"] for store in stores.values()),
    }

    report = {
        "schema_version": "retail-reconciliation-v1",
        "input_file_count": len(STORE_ORDER),
        "processed_store_count": len(STORE_ORDER),
        "store_order": STORE_ORDER,
        "duplicate_transaction_ids": sorted(duplicate_ids),
        "unmapped_skus": sorted({sku for store in stores.values() for sku in store["unmapped_skus"]}),
        "stores": stores,
        "categories": categories,
        "totals": totals,
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
PY
