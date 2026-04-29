import csv
import json
from collections import Counter, defaultdict
from operator import add
from pathlib import Path
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


INPUT_ROOT = Path("/input_artifacts")
OUTPUT_PATH = Path("/logs/agent/output.json")

STORE_FILES = [
    "atlanta.csv",
    "boston.csv",
    "chicago.csv",
    "denver.csv",
    "el_paso.csv",
    "fresno.csv",
    "grand_rapids.csv",
    "houston.csv",
    "indianapolis.csv",
    "jackson.csv",
]

ID_COLUMNS = ["transaction_id", "txn_id", "id", "order_no", "receipt", "transaction", "sale_id", "tid", "order_id"]
SKU_COLUMNS = ["sku", "item_code", "product", "sku_code", "product_sku", "item", "upc", "product_id"]
QTY_COLUMNS = ["quantity", "units", "qty", "count", "quantity_sold", "qty_sold", "number"]
PRICE_COLUMNS = ["unit_price", "price_each", "unit_cost", "unit_amount", "sale_price", "price", "each"]
TYPE_COLUMNS = ["transaction_type", "kind", "status", "action", "type", "mode", "operation", "txn_kind", "record_type"]

REFUND_WORDS = {"refund", "return", "returned", "refunded"}
CATEGORIES = ["beverages", "pantry", "household", "personal_care", "electronics", "UNMAPPED"]


class ReconcileState(TypedDict):
    catalog: dict[str, str]
    store_files: list[str]
    normalized_rows: Annotated[list[dict], add]
    report: dict


def first_value(row: dict, names: list[str]) -> str:
    for name in names:
        if name in row and str(row[name]).strip():
            return str(row[name]).strip()
    raise KeyError(f"Missing expected columns: {names}")


def money(value: float) -> float:
    return round(float(value) + 1e-9, 2)


def load_inputs(state: ReconcileState) -> dict:
    with (INPUT_ROOT / "products.csv").open(newline="") as handle:
        catalog = {
            row["sku"].strip(): row["category"].strip()
            for row in csv.DictReader(handle)
        }
    return {"catalog": catalog, "store_files": STORE_FILES, "normalized_rows": []}


def make_store_worker(filename: str):
    def store_worker(state: ReconcileState) -> dict:
        rows = []
        store_path = INPUT_ROOT / "stores" / filename
        store_name = Path(filename).stem

        with store_path.open(newline="") as handle:
            for row_index, row in enumerate(csv.DictReader(handle), start=1):
                txn_id = first_value(row, ID_COLUMNS)
                sku = first_value(row, SKU_COLUMNS)
                qty = float(first_value(row, QTY_COLUMNS))
                price = float(first_value(row, PRICE_COLUMNS))
                txn_type = first_value(row, TYPE_COLUMNS).lower()

                rows.append(
                    {
                        "store": store_name,
                        "filename": filename,
                        "row_index": row_index,
                        "txn_id": txn_id,
                        "sku": sku,
                        "qty": abs(qty),
                        "amount": abs(qty * price),
                        "is_refund": qty < 0 or txn_type in REFUND_WORDS,
                        "category": state["catalog"].get(sku, "UNMAPPED"),
                    }
                )

        return {"normalized_rows": rows}

    return store_worker


def reduce_and_reconcile(state: ReconcileState) -> dict:
    all_rows = sorted(state["normalized_rows"], key=lambda row: (row["filename"], row["row_index"]))
    id_counts = Counter(row["txn_id"] for row in all_rows)
    duplicate_ids = sorted(txn_id for txn_id, count in id_counts.items() if count > 1)

    stores = {}
    category_net = {category: 0.0 for category in CATEGORIES}
    sku_net_by_store = defaultdict(lambda: defaultdict(float))
    unmapped_global = set()
    seen = set()
    global_gross = 0.0
    global_refunds = 0.0
    global_units = 0

    for row in all_rows:
        if row["txn_id"] in seen:
            continue
        seen.add(row["txn_id"])

        store = row["store"]
        stores.setdefault(
            store,
            {
                "gross_sales": 0.0,
                "refunds": 0.0,
                "net_revenue": 0.0,
                "units_sold": 0,
                "top_sku_by_net_revenue": "",
                "unmapped_skus": set(),
            },
        )

        signed_amount = -row["amount"] if row["is_refund"] else row["amount"]
        category_net[row["category"]] += signed_amount
        sku_net_by_store[store][row["sku"]] += signed_amount

        if row["is_refund"]:
            stores[store]["refunds"] += row["amount"]
            global_refunds += row["amount"]
        else:
            stores[store]["gross_sales"] += row["amount"]
            stores[store]["units_sold"] += int(row["qty"])
            global_gross += row["amount"]
            global_units += int(row["qty"])

        if row["category"] == "UNMAPPED":
            stores[store]["unmapped_skus"].add(row["sku"])
            unmapped_global.add(row["sku"])

    for store, data in stores.items():
        data["gross_sales"] = money(data["gross_sales"])
        data["refunds"] = money(data["refunds"])
        data["net_revenue"] = money(data["gross_sales"] - data["refunds"])
        data["unmapped_skus"] = sorted(data["unmapped_skus"])
        data["top_sku_by_net_revenue"] = sorted(
            sku_net_by_store[store].items(),
            key=lambda item: (-money(item[1]), item[0]),
        )[0][0]

    report = {
        "stores": dict(sorted(stores.items())),
        "category_net_revenue": {category: money(category_net[category]) for category in CATEGORIES},
        "duplicate_transaction_ids": duplicate_ids,
        "global": {
            "gross_sales": money(global_gross),
            "refunds": money(global_refunds),
            "net_revenue": money(global_gross - global_refunds),
            "units_sold": global_units,
            "store_count": len(stores),
            "transaction_file_count": len(STORE_FILES),
            "unmapped_sku_count": len(unmapped_global),
        },
    }
    return {"report": report}


def write_output(state: ReconcileState) -> dict:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(state["report"], indent=2, sort_keys=True) + "\n")
    return {}


def build_graph():
    builder = StateGraph(ReconcileState)
    builder.add_node("load_inputs", load_inputs)

    worker_nodes = []
    for filename in STORE_FILES:
        node_name = f"worker_{Path(filename).stem}"
        worker_nodes.append(node_name)
        builder.add_node(node_name, make_store_worker(filename))

    builder.add_node("reduce_and_reconcile", reduce_and_reconcile)
    builder.add_node("write_output", write_output)

    builder.add_edge(START, "load_inputs")
    for node_name in worker_nodes:
        builder.add_edge("load_inputs", node_name)
    builder.add_edge(worker_nodes, "reduce_and_reconcile")
    builder.add_edge("reduce_and_reconcile", "write_output")
    builder.add_edge("write_output", END)

    return builder.compile()


if __name__ == "__main__":
    graph = build_graph()
    graph.invoke({"catalog": {}, "store_files": [], "normalized_rows": [], "report": {}})
