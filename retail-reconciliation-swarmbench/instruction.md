# Retail Reconciliation SwarmBench Task

You are given ten inconsistent retail transaction exports and one product catalog in `/environment/input_artifacts`.

Your task is to reconcile every store CSV into one normalized JSON report at:

```text
/workspace/report.json
```

The CSV files intentionally use different header names, date formats, transaction labels, and data conventions. They also include refunds, negative quantities, duplicate transaction IDs, and SKUs that are not present in the catalog.

## Input Files

Process these store files in this exact order:

1. `atlanta.csv`
2. `boston.csv`
3. `chicago.csv`
4. `denver.csv`
5. `el_paso.csv`
6. `fresno.csv`
7. `grand_rapids.csv`
8. `houston.csv`
9. `indianapolis.csv`
10. `jackson.csv`

Use `product_catalog.csv` to map known SKUs to product categories. Any SKU not present in the catalog must be assigned to the category `unknown` and included in `unmapped_skus`.

## Normalization Rules

Normalize every transaction to these canonical fields:

- `transaction_id`
- `store`
- `date`
- `sku`
- `quantity`
- `unit_price`
- `transaction_type`
- `category`
- `amount`

The store files use schema aliases. Examples include:

- transaction ID: `transaction_id`, `txn_id`, `id`, `order_no`, `receipt`, `transaction`, `sale_id`, `tid`, `transaction_ref`
- SKU: `sku`, `item_code`, `product`, `sku_code`, `product_sku`, `item`, `upc`, `product_id`
- quantity: `quantity`, `units`, `qty`, `count`, `quantity_sold`, `qty_sold`, `number`, `item_qty`
- unit price: `unit_price`, `price_each`, `unit_cost`, `unit_amount`, `sale_price`, `price`, `each`, `amount_per_unit`
- transaction type: `transaction_type`, `kind`, `status`, `action`, `type`, `mode`, `operation`, `txn_kind`, `event`

Treat `sale`, `order`, and `sold` as sales. Treat `refund`, `return`, and `returned` as refunds. A negative quantity is always a refund even if the transaction label is ambiguous.

Financial amounts must be computed as:

```text
amount = abs(quantity) * unit_price
```

Sales add to `gross_sales`. Refunds add to `refunds` and subtract from `net_revenue`.

## Duplicate Rule

Duplicate transaction IDs can appear across stores. Process files in the required store order above and keep only the first occurrence of each `transaction_id`. Later occurrences must be excluded from all store, category, and global totals, but the duplicate ID must be reported in `duplicate_transaction_ids`.

## Required Output Schema

Write a JSON object with this shape:

```json
{
  "schema_version": "retail-reconciliation-v1",
  "input_file_count": 10,
  "processed_store_count": 10,
  "store_order": ["atlanta", "boston", "..."],
  "duplicate_transaction_ids": ["..."],
  "unmapped_skus": ["..."],
  "stores": {
    "atlanta": {
      "raw_row_count": 10,
      "deduped_transaction_count": 10,
      "sale_count": 8,
      "refund_count": 2,
      "gross_sales": 334.09,
      "refunds": 10.75,
      "net_revenue": 323.34,
      "units_sold": 41,
      "units_refunded": 3,
      "unmapped_skus": ["SKU-9999"]
    }
  },
  "categories": {
    "beverages": {
      "transaction_count": 20,
      "gross_sales": 533.30,
      "refunds": 5.00,
      "net_revenue": 528.30,
      "units_sold": 245,
      "units_refunded": 2
    }
  },
  "totals": {
    "raw_row_count": 100,
    "deduped_transaction_count": 96,
    "sale_count": 85,
    "refund_count": 11,
    "gross_sales": 4006.67,
    "refunds": 327.63,
    "net_revenue": 3679.04,
    "units_sold": 564,
    "units_refunded": 16
  }
}
```

Round monetary fields to two decimal places. Lists may be emitted in any order, but the verifier will compare them as sets.
