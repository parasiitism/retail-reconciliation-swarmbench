#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from verify import load_json, score_report


def main():
    report_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace/report.json"
    oracle_path = Path(__file__).with_name("oracle.json")

    try:
        report = load_json(report_path)
        oracle = load_json(oracle_path)
        result = score_report(report, oracle)
    except Exception as exc:
        result = {
            "reward": 0.0,
            "breakdown": {},
            "failures": [f"{type(exc).__name__}: {exc}"],
        }

    print(json.dumps({"reward": result["reward"], "metadata": result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
