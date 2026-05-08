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


def normalize_column_name(value: str) -> str:
    return value.strip().lower()


def get_value(
    row: dict[str, str],
    canonical_field: str,
    field_mapping: dict[str, str] | None = None,
    required: bool = True,
    default: str = "",
) -> str:
    if field_mapping:
        mapped_column = field_mapping.get(canonical_field)

        if mapped_column:
            if mapped_column in row:
                return row[mapped_column]

            normalized_row = {
                normalize_column_name(column): value
                for column, value in row.items()
            }
            normalized_mapped_column = normalize_column_name(mapped_column)

            if normalized_mapped_column in normalized_row:
                return normalized_row[normalized_mapped_column]

            if required:
                available_columns = ", ".join(row.keys())
                raise KeyError(
                    f"Mapped column '{mapped_column}' for '{canonical_field}' "
                    f"was not found. Available columns: {available_columns}"
                )

            return default

    aliases = SCHEMA_ALIASES.get(canonical_field)

    if aliases is None:
        raise KeyError(f"Unknown canonical field: {canonical_field}")

    for alias in aliases:
        if alias in row:
            return row[alias]

    normalized_row = {
        normalize_column_name(column): value
        for column, value in row.items()
    }

    for alias in aliases:
        normalized_alias = normalize_column_name(alias)
        if normalized_alias in normalized_row:
            return normalized_row[normalized_alias]

    if not required:
        return default

    available_columns = ", ".join(row.keys())
    expected_columns = ", ".join(aliases)
    raise KeyError(
        f"Could not find '{canonical_field}'. "
        f"Expected one of: {expected_columns}. "
        f"Available columns: {available_columns}"
    )
