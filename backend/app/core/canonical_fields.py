RETAIL_REQUIRED_CANONICAL_FIELDS = [
    "transaction_id",
    "transaction_date",
    "sku",
    "quantity",
    "unit_price",
]

RETAIL_OPTIONAL_CANONICAL_FIELDS = [
    "transaction_type",
]

RETAIL_CANONICAL_FIELDS = (
    RETAIL_REQUIRED_CANONICAL_FIELDS + RETAIL_OPTIONAL_CANONICAL_FIELDS
)


def normalize_column_name(value: str) -> str:
    return value.strip().lower()


def validate_field_mapping(
    field_mapping: dict[str, str],
    csv_headers: list[str],
) -> dict:
    normalized_headers = {
        normalize_column_name(header): header
        for header in csv_headers
    }

    missing_required_fields = [
        field
        for field in RETAIL_REQUIRED_CANONICAL_FIELDS
        if not field_mapping.get(field)
    ]

    unknown_canonical_fields = [
        field
        for field in field_mapping
        if field not in RETAIL_CANONICAL_FIELDS
    ]

    mapped_unknown_columns = [
        source_column
        for source_column in field_mapping.values()
        if normalize_column_name(source_column) not in normalized_headers
    ]

    mapped_columns = [
        normalize_column_name(source_column)
        for source_column in field_mapping.values()
    ]

    duplicate_mapped_columns = sorted({
        column
        for column in mapped_columns
        if mapped_columns.count(column) > 1
    })

    issues = []

    if missing_required_fields:
        issues.append({
            "type": "missing_required_canonical_fields",
            "fields": missing_required_fields,
        })

    if unknown_canonical_fields:
        issues.append({
            "type": "unknown_canonical_fields",
            "fields": unknown_canonical_fields,
        })

    if mapped_unknown_columns:
        issues.append({
            "type": "mapped_columns_not_found_in_csv",
            "columns": mapped_unknown_columns,
        })

    if duplicate_mapped_columns:
        issues.append({
            "type": "duplicate_source_columns",
            "columns": duplicate_mapped_columns,
        })

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
    }
