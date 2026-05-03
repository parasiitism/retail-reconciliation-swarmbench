import csv
import sys
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.app.core.config import SAMPLE_RETAIL_DIR


def reconcile_one_file(csv_path: Path) -> dict[str, Decimal]:
    sales = Decimal("0.00")
    refunds = Decimal("0.00")

    with csv_path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            quantity = Decimal(row["quantity"])
            price = Decimal(row["unit_price"])
            amount = quantity * price

            if row["transaction_type"] == "sale":
                sales += amount

            if row["transaction_type"] == "refund":
                refunds += abs(amount)

    return {
        "sales": sales,
        "refunds": refunds,
        "net_revenue": sales - refunds,
    }


if __name__ == "__main__":
    totals = reconcile_one_file(SAMPLE_RETAIL_DIR / "atlanta.csv")
    print("Sales", totals["sales"])
    print("Refund:", totals["refunds"])
    print("Net Revenue", totals["net_revenue"])
