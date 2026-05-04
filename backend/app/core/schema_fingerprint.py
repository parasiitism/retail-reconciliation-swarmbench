import hashlib


def normalize_header(header: str) -> str:
    return (
        header.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
    )


def build_ordered_fingerprint(headers: list[str]) -> str:
    normalized_headers = [normalize_header(header) for header in headers]
    fingerprint_input = "|".join(normalized_headers)

    return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()


def build_unordered_fingerprint(headers: list[str]) -> str:
    normalized_headers = sorted(normalize_header(header) for header in headers)
    fingerprint_input = "|".join(normalized_headers)

    return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
