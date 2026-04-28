# Retail Transaction Reconciliation

## Background

A regional retailer exported January 2026 transaction files from ten store systems. The store systems use different column names and conventions, but all files describe point-of-sale transactions. The product catalog is available at `/input_artifacts/products.csv`, and store transaction files are in `/input_artifacts/stores/`.

## Task

Analyze every CSV file in `/input_artifacts/stores/` and produce a consolidated JSON report at:

`/logs/agent/output.json`

The report must reconcile all stores using the product catalog and the normalization rules below.

## Normalization Rules

- Transaction ID columns may be named `transaction_id`, `txn_id`, `id`, `order_no`, `receipt`, `transaction`, `sale_id`, `tid`, or `order_id`.
- SKU columns may be named `sku`, `item_code`, `product`, `sku_code`, `product_sku`, `item`, `upc`, or `product_id`.
- Quantity columns may be named `quantity`, `units`, `qty`, `count`, `quantity_sold`, `qty_sold`, or `number`.
- Unit price columns may be named `unit_price`, `price_each`, `unit_cost`, `unit_amount`, `sale_price`, `price`, or `each`.
- Transaction type columns may be named `transaction_type`, `kind`, `status`, `action`, `type`, `mode`, `operation`, `txn_kind`, or `record_type`.
- Treat `refund`, `return`, `returned`, and `refunded` as refund rows, case-insensitively.
- Treat a negative quantity as a refund even if the transaction type is not explicit.
- For each transaction ID that appears more than once across all store files, keep only the first occurrence when computing financial totals. The first occurrence is determined by alphabetical store filename, then row order within that file.
- Still report every duplicate transaction ID in the final `duplicate_transaction_ids` array.
- Gross sales are the sum of non-refund row amounts after duplicate removal.
- Refunds are the absolute value of refund row amounts after duplicate removal.
- Net revenue is `gross_sales - refunds`.
- Units sold count only non-refund units after duplicate removal.
- Rows with SKUs missing from the product catalog still count in financial totals and must be assigned to category `UNMAPPED`.
- Monetary values must be rounded to two decimals.

## Required Output Shape

Write valid JSON with exactly these top-level keys:

```json
{
  "stores": {
    "atlanta": {
      "gross_sales": 0.0,
      "refunds": 0.0,
      "net_revenue": 0.0,
      "units_sold": 0,
      "top_sku_by_net_revenue": "SKU-0000",
      "unmapped_skus": []
    }
  },
  "category_net_revenue": {
    "beverages": 0.0,
    "pantry": 0.0,
    "household": 0.0,
    "personal_care": 0.0,
    "electronics": 0.0,
    "UNMAPPED": 0.0
  },
  "duplicate_transaction_ids": [],
  "global": {
    "gross_sales": 0.0,
    "refunds": 0.0,
    "net_revenue": 0.0,
    "units_sold": 0,
    "store_count": 10,
    "transaction_file_count": 10,
    "unmapped_sku_count": 0
  }
}
```

Use the store filename without `.csv` as the store key. Sort arrays lexicographically. Include all categories shown above, even if a category total is zero.

## Success Criteria

The answer is successful when `/logs/agent/output.json` exists, is valid JSON, covers all ten store files, correctly handles schema differences, duplicate transaction IDs, refunds, missing SKU mappings, per-store summaries, category totals, and global totals.
