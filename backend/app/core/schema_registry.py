from datetime import datetime, timezone
from uuid import uuid4


SCHEMA_REGISTRY: dict[str, dict] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_schema_draft(profile: dict) -> dict:
    return {
        "schema_id": str(uuid4()),
        "schema_name": f"Draft schema for {profile['filename']}",
        "company_name": None,
        "status": "draft",
        "headers": profile["headers"],
        "ordered_fingerprint": profile["ordered_fingerprint"],
        "unordered_fingerprint": profile["unordered_fingerprint"],
        "field_mapping": {},
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def find_schema_by_fingerprint(unordered_fingerprint: str) -> dict | None:
    return SCHEMA_REGISTRY.get(unordered_fingerprint)


def register_schema(schema: dict) -> dict:
    schema["status"] = "active"
    schema["updated_at"] = utc_now()

    SCHEMA_REGISTRY[schema["unordered_fingerprint"]] = schema

    return schema


def resolve_schema(profile: dict) -> dict:
    existing_schema = find_schema_by_fingerprint(profile["unordered_fingerprint"])

    if existing_schema is not None:
        return {
            "match_type": "exact_match",
            "match_confidence": 1.0,
            "schema": existing_schema,
            "message": "Exact schema fingerprint match found.",
        }

    draft_schema = create_schema_draft(profile)

    return {
        "match_type": "new_schema_required",
        "match_confidence": 0.0,
        "schema": draft_schema,
        "message": "No exact schema fingerprint match found. Create a new schema.",
    }
