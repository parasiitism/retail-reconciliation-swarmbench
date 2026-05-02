SCHEMA_ALIASES = {
    "transaction_id": [
        "transaction_id",
        "txn_id",
        "id",
        "order_no",
        "receipt",
        "transaction",
        "sale_id",
        "tid",
        "transaction_ref",
    ],
    "transaction_date": [
        "date",
        "txn_date",
        "sold_at",
        "day",
        "date_sold",
        "business_date",
        "when",
        "store_day",
    ],
    "sku": [
        "sku",
        "item_code",
        "product",
        "sku_code",
        "product_sku",
        "item",
        "upc",
        "product_id",
    ],
    "quantity": [
        "quantity",
        "units",
        "qty",
        "count",
        "quantity_sold",
        "qty_sold",
        "number",
        "item_qty",
    ],
    "unit_price": [
        "unit_price",
        "price_each",
        "unit_cost",
        "unit_amount",
        "sale_price",
        "price",
        "each",
        "amount_per_unit",
    ],
    "transaction_type": [
        "transaction_type",
        "kind",
        "status",
        "action",
        "type",
        "mode",
        "operation",
        "txn_kind",
        "event",
    ],
}


def get_value(row: dict[str, str], canonical_field: str) -> str:
    aliases = SCHEMA_ALIASES.get(canonical_field)
    if aliases is None:
        raise KeyError(f"Unknown canonical field: {canonical_field}")

    for alias in aliases:
        if alias in row:
            return row[alias]

    available_columns = ", ".join(row.keys())
    expected_columns = ", ".join(aliases)
    raise KeyError(
        f"Could not find '{canonical_field}'. "
        f"Expected one of: {expected_columns}. "
        f"Available columns: {available_columns}"
    )
