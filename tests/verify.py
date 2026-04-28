import csv
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = Path(os.environ.get("INPUT_ARTIFACTS", "/input_artifacts"))
OUTPUT = Path(os.environ.get("AGENT_OUTPUT", "/logs/agent/output.json"))
REWARD = Path(os.environ.get("REWARD_FILE", "/logs/verifier/reward.txt"))
CATALOG = INPUT_ROOT / "products.csv"
STORES = INPUT_ROOT / "stores"

ID_COLUMNS = ["transaction_id", "txn_id", "id", "order_no", "receipt", "transaction", "sale_id", "tid", "order_id"]
SKU_COLUMNS = ["sku", "item_code", "product", "sku_code", "product_sku", "item", "upc", "product_id"]
QTY_COLUMNS = ["quantity", "units", "qty", "count", "quantity_sold", "qty_sold", "number"]
PRICE_COLUMNS = ["unit_price", "price_each", "unit_cost", "unit_amount", "sale_price", "price", "each"]
TYPE_COLUMNS = ["transaction_type", "kind", "status", "action", "type", "mode", "operation", "txn_kind", "record_type"]
REFUND_WORDS = {"refund", "return", "returned", "refunded"}
CANONICAL_CATEGORIES = ["beverages", "pantry", "household", "personal_care", "electronics", "UNMAPPED"]


def first_value(row, names):
    for name in names:
        if name in row and str(row[name]).strip() != "":
            return str(row[name]).strip()
    raise KeyError(f"missing one of {names}")


def money(value):
    return round(float(value) + 1e-9, 2)


def load_catalog():
    with CATALOG.open(newline="") as handle:
        return {row["sku"].strip(): row["category"].strip() for row in csv.DictReader(handle)}


def build_expected():
    catalog = load_catalog()
    all_rows = []
    id_counts = Counter()

    for store_file in sorted(STORES.glob("*.csv")):
        store = store_file.stem
        with store_file.open(newline="") as handle:
            for row_index, row in enumerate(csv.DictReader(handle), start=1):
                txn_id = first_value(row, ID_COLUMNS)
                sku = first_value(row, SKU_COLUMNS)
                qty = float(first_value(row, QTY_COLUMNS))
                price = float(first_value(row, PRICE_COLUMNS))
                txn_type = first_value(row, TYPE_COLUMNS).lower()
                is_refund = qty < 0 or txn_type in REFUND_WORDS
                amount = abs(qty * price)
                category = catalog.get(sku, "UNMAPPED")
                all_rows.append(
                    {
                        "store": store,
                        "row_index": row_index,
                        "txn_id": txn_id,
                        "sku": sku,
                        "qty": abs(qty),
                        "amount": amount,
                        "is_refund": is_refund,
                        "category": category,
                    }
                )
                id_counts[txn_id] += 1

    duplicate_ids = sorted([txn_id for txn_id, count in id_counts.items() if count > 1])
    seen = set()
    stores = {}
    category_net = {category: 0.0 for category in CANONICAL_CATEGORIES}
    global_totals = {"gross_sales": 0.0, "refunds": 0.0, "units_sold": 0}
    unmapped_global = set()
    sku_net_by_store = defaultdict(lambda: defaultdict(float))

    for row in all_rows:
        if row["txn_id"] in seen:
            continue
        seen.add(row["txn_id"])

        store = row["store"]
        if store not in stores:
            stores[store] = {
                "gross_sales": 0.0,
                "refunds": 0.0,
                "net_revenue": 0.0,
                "units_sold": 0,
                "top_sku_by_net_revenue": "",
                "unmapped_skus": set(),
            }

        signed = -row["amount"] if row["is_refund"] else row["amount"]
        category_net[row["category"]] += signed
        sku_net_by_store[store][row["sku"]] += signed

        if row["is_refund"]:
            stores[store]["refunds"] += row["amount"]
            global_totals["refunds"] += row["amount"]
        else:
            stores[store]["gross_sales"] += row["amount"]
            stores[store]["units_sold"] += int(row["qty"])
            global_totals["gross_sales"] += row["amount"]
            global_totals["units_sold"] += int(row["qty"])

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

    expected = {
        "stores": dict(sorted(stores.items())),
        "category_net_revenue": {category: money(category_net[category]) for category in CANONICAL_CATEGORIES},
        "duplicate_transaction_ids": duplicate_ids,
        "global": {
            "gross_sales": money(global_totals["gross_sales"]),
            "refunds": money(global_totals["refunds"]),
            "net_revenue": money(global_totals["gross_sales"] - global_totals["refunds"]),
            "units_sold": global_totals["units_sold"],
            "store_count": len(stores),
            "transaction_file_count": len(list(STORES.glob("*.csv"))),
            "unmapped_sku_count": len(unmapped_global),
        },
    }
    return expected


def close_enough(actual, expected):
    if isinstance(expected, float):
        try:
            return math.isclose(float(actual), expected, abs_tol=0.01)
        except Exception:
            return False
    if isinstance(expected, int):
        return actual == expected
    return actual == expected


def compare_mapping(actual, expected):
    if not isinstance(actual, dict):
        return False
    for key, value in expected.items():
        if key not in actual or not close_enough(actual[key], value):
            return False
    return True


def main():
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    checks = []

    def add(name, passed, weight):
        checks.append((name, bool(passed), weight))

    expected = build_expected()

    if not OUTPUT.exists():
        add("output_json_exists", False, 1.0)
        REWARD.write_text("0")
        print("output_json_exists: FAIL (1.0)")
        return 1

    try:
        actual = json.loads(OUTPUT.read_text())
        add("valid_json", True, 0.05)
    except Exception as exc:
        add("valid_json", False, 1.0)
        REWARD.write_text("0")
        print(f"valid_json: FAIL (1.0) {exc}")
        return 1

    add("top_level_keys", set(actual.keys()) == {"stores", "category_net_revenue", "duplicate_transaction_ids", "global"}, 0.05)
    add("all_stores_present", sorted(actual.get("stores", {}).keys()) == sorted(expected["stores"].keys()), 0.10)
    add("duplicate_ids", actual.get("duplicate_transaction_ids") == expected["duplicate_transaction_ids"], 0.10)
    add("category_totals", compare_mapping(actual.get("category_net_revenue"), expected["category_net_revenue"]), 0.15)
    add("global_totals", compare_mapping(actual.get("global"), expected["global"]), 0.15)

    store_weight = 0.40 / len(expected["stores"])
    for store, expected_store in expected["stores"].items():
        actual_store = actual.get("stores", {}).get(store)
        add(f"store_{store}", compare_mapping(actual_store, expected_store), store_weight)

    score = round(sum(weight for _, passed, weight in checks if passed), 4)
    if score > 0.999:
        score = 1.0
    REWARD.write_text(str(score))

    for name, passed, weight in checks:
        print(f"{name}: {'PASS' if passed else 'FAIL'} ({weight:.4f})")
    print(f"reward: {score}")
    return 0 if score == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
