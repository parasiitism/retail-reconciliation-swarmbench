import csv
from pathlib import Path


def load_product_catalog(catalog_path: Path) -> dict[str, str]:
    if not catalog_path.exists():
        raise FileNotFoundError(f"Product catalog not found: {catalog_path}")

    catalog: dict[str, str] = {}

    with catalog_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            sku = row.get("sku", "").strip()
            category = row.get("category", "").strip()

            if not sku:
                continue

            catalog[sku] = category or "unknown"

    return catalog
