import csv
from pathlib import Path

from backend.app.core.schema_fingerprint import (
    build_ordered_fingerprint,
    build_unordered_fingerprint,
    normalize_header,
)
from backend.app.core.schema_mapping import SCHEMA_ALIASES


PROFILE_SAMPLE_LIMIT = 5


def infer_value_type(values: list[str]) -> str:
    cleaned_values = [value for value in values if value != ""]

    if not cleaned_values:
        return "empty"

    numeric_count = 0

    for value in cleaned_values:
        try:
            float(value)
            numeric_count += 1
        except ValueError:
            pass

    if numeric_count == len(cleaned_values):
        return "number"

    date_like_count = sum(
        1
        for value in cleaned_values
        if "-" in value or "/" in value
    )

    if date_like_count >= max(1, len(cleaned_values) // 2):
        return "date_like"

    return "text"


def suggest_canonical_field(column_name: str, sample_values: list[str]) -> dict:
    normalized_column = normalize_header(column_name)

    for canonical_field, aliases in SCHEMA_ALIASES.items():
        normalized_aliases = [normalize_header(alias) for alias in aliases]

        if normalized_column in normalized_aliases:
            return {
                "suggested_field": canonical_field,
                "confidence": 0.95,
                "reason": "Column name directly matched a known schema alias.",
            }

    for canonical_field, aliases in SCHEMA_ALIASES.items():
        normalized_aliases = [normalize_header(alias) for alias in aliases]

        if any(alias in normalized_column for alias in normalized_aliases):
            return {
                "suggested_field": canonical_field,
                "confidence": 0.75,
                "reason": "Column name partially matched a known schema alias.",
            }

    value_type = infer_value_type(sample_values)

    if value_type == "date_like":
        return {
            "suggested_field": "transaction_date",
            "confidence": 0.55,
            "reason": "Sample values look like dates.",
        }

    return {
        "suggested_field": None,
        "confidence": 0.0,
        "reason": "No reliable mapping suggestion found.",
    }


def profile_csv(csv_path: Path) -> dict:
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    headers = reader.fieldnames or []
    column_profiles = []

    for header in headers:
        values = [(row.get(header) or "").strip() for row in rows]
        non_empty_values = [value for value in values if value]
        sample_values = non_empty_values[:PROFILE_SAMPLE_LIMIT]
        suggestion = suggest_canonical_field(header, sample_values)

        column_profiles.append(
            {
                "name": header,
                "normalized_name": normalize_header(header),
                "empty_count": len(values) - len(non_empty_values),
                "unique_count": len(set(non_empty_values)),
                "sample_values": sample_values,
                "inferred_type": infer_value_type(sample_values),
                "suggested_field": suggestion["suggested_field"],
                "confidence": suggestion["confidence"],
                "reason": suggestion["reason"],
            }
        )

    return {
        "filename": csv_path.name,
        "row_count": len(rows),
        "column_count": len(headers),
        "headers": headers,
        "ordered_fingerprint": build_ordered_fingerprint(headers),
        "unordered_fingerprint": build_unordered_fingerprint(headers),
        "columns": column_profiles,
    }
