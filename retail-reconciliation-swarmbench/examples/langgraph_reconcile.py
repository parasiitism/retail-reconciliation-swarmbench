#!/usr/bin/env python3
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Annotated, Any, TypedDict

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:
    END = START = StateGraph = None


HERE = Path(__file__).resolve()
TASK_ROOT = HERE.parents[1]
DEFAULT_INPUT_DIR = Path("/environment/input_artifacts")
if not DEFAULT_INPUT_DIR.exists():
    DEFAULT_INPUT_DIR = TASK_ROOT / "environment" / "input_artifacts"
DEFAULT_OUTPUT = Path("/workspace/report.json")
if not DEFAULT_OUTPUT.parent.exists():
    DEFAULT_OUTPUT = TASK_ROOT / "report.json"

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
REFUND_TYPES = {"refund", "return", "returned"}


def merge_partials(left: dict[str, Any] | None, right: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


class ReconcileState(TypedDict, total=False):
    input_dir: str
    output_path: str
    catalog: dict[str, str]
    partials: Annotated[dict[str, Any], merge_partials]
    report: dict[str, Any]


def first(row: dict[str, str], key: str) -> str:
    for name in ALIASES[key]:
        if name in row:
            return row[name]
    raise KeyError(f"missing {key} in columns {sorted(row)}")


def money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def load_catalog(input_dir: Path) -> dict[str, str]:
    with (input_dir / "product_catalog.csv").open("r", encoding="utf-8", newline="") as handle:
        return {row["sku"]: row["category"] for row in csv.DictReader(handle)}


def normalise_store(input_dir: Path, store: str, catalog: dict[str, str]) -> dict[str, Any]:
    path = input_dir / f"{store}.csv"
    transactions = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row_index, row in enumerate(csv.DictReader(handle)):
            quantity = Decimal(first(row, "quantity"))
            unit_price = Decimal(first(row, "unit_price"))
            label = first(row, "transaction_type").strip().lower()
            transaction_type = "refund" if quantity < 0 or label in REFUND_TYPES else "sale"
            sku = first(row, "sku")
            transactions.append(
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
    return {"raw_row_count": len(transactions), "transactions": transactions}


def blank_store() -> dict[str, Any]:
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


def blank_category() -> dict[str, Any]:
    return {
        "transaction_count": 0,
        "gross_sales": Decimal("0"),
        "refunds": Decimal("0"),
        "net_revenue": Decimal("0"),
        "units_sold": 0,
        "units_refunded": 0,
    }


def apply_transaction(store_stats: dict[str, Any], category_stats: dict[str, Any], tx: dict[str, Any]) -> None:
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


def serialise_store(stats: dict[str, Any]) -> dict[str, Any]:
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


def serialise_category(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "transaction_count": stats["transaction_count"],
        "gross_sales": money(stats["gross_sales"]),
        "refunds": money(stats["refunds"]),
        "net_revenue": money(stats["net_revenue"]),
        "units_sold": stats["units_sold"],
        "units_refunded": stats["units_refunded"],
    }


def reduce_partials(partials: dict[str, Any]) -> dict[str, Any]:
    store_stats = {store: blank_store() for store in STORE_ORDER}
    category_stats = {category: blank_category() for category in CATEGORY_ORDER}
    seen = set()
    duplicate_ids = set()

    for store in STORE_ORDER:
        shard = partials[store]
        store_stats[store]["raw_row_count"] = shard["raw_row_count"]
        for tx in shard["transactions"]:
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
    return {
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


def load_inputs(state: ReconcileState) -> ReconcileState:
    input_dir = Path(state.get("input_dir", str(DEFAULT_INPUT_DIR)))
    return {
        "input_dir": str(input_dir),
        "output_path": state.get("output_path", str(DEFAULT_OUTPUT)),
        "catalog": load_catalog(input_dir),
        "partials": {},
    }


def make_worker(store: str):
    def worker(state: ReconcileState) -> ReconcileState:
        input_dir = Path(state["input_dir"])
        return {"partials": {store: normalise_store(input_dir, store, state["catalog"])}}

    worker.__name__ = f"worker_{store}"
    return worker


def reduce_and_reconcile(state: ReconcileState) -> ReconcileState:
    return {"report": reduce_partials(state["partials"])}


def write_output(state: ReconcileState) -> ReconcileState:
    output_path = Path(state.get("output_path", str(DEFAULT_OUTPUT)))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(state["report"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {}


def run_sequential(input_dir: Path, output_path: Path) -> None:
    catalog = load_catalog(input_dir)
    partials = {store: normalise_store(input_dir, store, catalog) for store in STORE_ORDER}
    report = reduce_partials(partials)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_graph():
    graph = StateGraph(ReconcileState)
    graph.add_node("load_inputs", load_inputs)
    graph.add_node("reduce_and_reconcile", reduce_and_reconcile)
    graph.add_node("write_output", write_output)
    graph.add_edge(START, "load_inputs")
    for store in STORE_ORDER:
        node_name = f"worker_{store}"
        graph.add_node(node_name, make_worker(store))
        graph.add_edge("load_inputs", node_name)
        graph.add_edge(node_name, "reduce_and_reconcile")
    graph.add_edge("reduce_and_reconcile", "write_output")
    graph.add_edge("write_output", END)
    return graph.compile()


def main() -> None:
    if StateGraph is None:
        print("langgraph is not installed; running the same map-reduce pipeline sequentially.")
        run_sequential(DEFAULT_INPUT_DIR, DEFAULT_OUTPUT)
        return

    app = build_graph()
    app.invoke({"input_dir": str(DEFAULT_INPUT_DIR), "output_path": str(DEFAULT_OUTPUT)})


if __name__ == "__main__":
    main()
