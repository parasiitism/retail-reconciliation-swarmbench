#!/usr/bin/env python3
import argparse
import json
import math
import sys
from pathlib import Path

MONEY_FIELDS = {"gross_sales", "refunds", "net_revenue"}
STORE_FIELDS = [
    "raw_row_count",
    "deduped_transaction_count",
    "sale_count",
    "refund_count",
    "gross_sales",
    "refunds",
    "net_revenue",
    "units_sold",
    "units_refunded",
    "unmapped_skus",
]
CATEGORY_FIELDS = [
    "transaction_count",
    "gross_sales",
    "refunds",
    "net_revenue",
    "units_sold",
    "units_refunded",
]
TOTAL_FIELDS = [
    "raw_row_count",
    "deduped_transaction_count",
    "sale_count",
    "refund_count",
    "gross_sales",
    "refunds",
    "net_revenue",
    "units_sold",
    "units_refunded",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def values_match(actual, expected, field):
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return False
        return sorted(str(item) for item in actual) == sorted(str(item) for item in expected)
    if field in MONEY_FIELDS:
        actual_float = as_float(actual)
        if actual_float is None:
            return False
        return math.isclose(actual_float, float(expected), rel_tol=0, abs_tol=0.01)
    if isinstance(expected, int):
        actual_float = as_float(actual)
        return actual_float is not None and actual_float == expected
    return actual == expected


def fraction(matches, total):
    return 0.0 if total == 0 else matches / total


def score_named_metrics(actual_section, expected_section, fields):
    matches = 0
    total = 0
    failures = []
    actual_section = actual_section if isinstance(actual_section, dict) else {}
    for name, expected_metrics in expected_section.items():
        actual_metrics = actual_section.get(name, {})
        if not isinstance(actual_metrics, dict):
            actual_metrics = {}
        for field in fields:
            total += 1
            expected_value = expected_metrics[field]
            actual_value = actual_metrics.get(field)
            if values_match(actual_value, expected_value, field):
                matches += 1
            else:
                failures.append(f"{name}.{field}")
    return fraction(matches, total), failures


def score_top_level_schema(report, oracle):
    checks = []
    checks.append(report.get("schema_version") == oracle["schema_version"])
    checks.append(
        report.get("input_file_count") == oracle["input_file_count"]
        and report.get("processed_store_count") == oracle["processed_store_count"]
    )
    checks.append(all(key in report for key in ["stores", "categories", "totals", "duplicate_transaction_ids", "unmapped_skus"]))
    checks.append(values_match(report.get("store_order"), oracle["store_order"], "store_order"))
    checks.append(
        isinstance(report.get("stores"), dict)
        and set(report["stores"]) == set(oracle["stores"])
        and isinstance(report.get("categories"), dict)
        and set(report["categories"]) == set(oracle["categories"])
    )
    return fraction(sum(1 for item in checks if item), len(checks))


def score_duplicates(report, oracle):
    checks = []
    checks.append(values_match(report.get("duplicate_transaction_ids"), oracle["duplicate_transaction_ids"], "duplicate_transaction_ids"))
    totals = report.get("totals", {}) if isinstance(report.get("totals"), dict) else {}
    checks.append(values_match(totals.get("deduped_transaction_count"), oracle["totals"]["deduped_transaction_count"], "deduped_transaction_count"))
    checks.append(values_match(totals.get("sale_count"), oracle["totals"]["sale_count"], "sale_count"))
    checks.append(values_match(totals.get("refund_count"), oracle["totals"]["refund_count"], "refund_count"))
    store_actual = report.get("stores", {}) if isinstance(report.get("stores"), dict) else {}
    per_store = 0
    for store, expected in oracle["stores"].items():
        actual = store_actual.get(store, {})
        if isinstance(actual, dict) and values_match(actual.get("deduped_transaction_count"), expected["deduped_transaction_count"], "deduped_transaction_count"):
            per_store += 1
    checks.append(per_store == len(oracle["stores"]))
    return fraction(sum(1 for item in checks if item), len(checks))


def score_report(report, oracle):
    if not isinstance(report, dict):
        return {
            "reward": 0.0,
            "breakdown": {},
            "failures": ["report is not a JSON object"],
        }

    schema_score = score_top_level_schema(report, oracle)
    duplicate_score = score_duplicates(report, oracle)
    store_score, store_failures = score_named_metrics(report.get("stores"), oracle["stores"], STORE_FIELDS)
    category_score, category_failures = score_named_metrics(report.get("categories"), oracle["categories"], CATEGORY_FIELDS)

    total_matches = 0
    total_failures = []
    actual_totals = report.get("totals", {}) if isinstance(report.get("totals"), dict) else {}
    for field in TOTAL_FIELDS:
        if values_match(actual_totals.get(field), oracle["totals"][field], field):
            total_matches += 1
        else:
            total_failures.append(f"totals.{field}")
    totals_score = fraction(total_matches, len(TOTAL_FIELDS))

    reward = (
        0.20 * schema_score
        + 0.15 * duplicate_score
        + 0.30 * store_score
        + 0.15 * category_score
        + 0.20 * totals_score
    )

    return {
        "reward": round(reward, 6),
        "breakdown": {
            "schema_normalization": round(schema_score, 6),
            "duplicate_handling": round(duplicate_score, 6),
            "per_store_metrics": round(store_score, 6),
            "category_totals": round(category_score, 6),
            "global_totals": round(totals_score, 6),
        },
        "failures": (store_failures + category_failures + total_failures)[:50],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", nargs="?", default="/workspace/report.json")
    parser.add_argument("--oracle", default=str(Path(__file__).with_name("oracle.json")))
    parser.add_argument("--assert-full", action="store_true")
    args = parser.parse_args()

    try:
        report = load_json(args.report)
        oracle = load_json(args.oracle)
        result = score_report(report, oracle)
    except Exception as exc:
        result = {
            "reward": 0.0,
            "breakdown": {},
            "failures": [f"{type(exc).__name__}: {exc}"],
        }

    print(json.dumps(result, indent=2, sort_keys=True))
    if args.assert_full and result["reward"] < 1.0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
