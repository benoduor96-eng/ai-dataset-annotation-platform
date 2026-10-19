"""Validation helpers shared by import and annotation APIs."""
from collections.abc import Mapping


class PayloadValidationError(ValueError):
    """A client supplied a structurally invalid annotation payload."""


def validate_task_payload(payload):
    """Require a JSON object with a useful payload and a bounded shape."""
    if not isinstance(payload, Mapping):
        raise PayloadValidationError("Task payload must be a JSON object.")
    if not payload:
        raise PayloadValidationError("Task payload must not be empty.")
    if len(payload) > 100:
        raise PayloadValidationError("Task payload has too many top-level fields.")
    return dict(payload)


def validate_schema_labels(labels):
    """Validate the common list-of-labels representation."""
    if not isinstance(labels, list):
        raise PayloadValidationError("Schema labels must be a list.")
    if len(labels) > 1000:
        raise PayloadValidationError("Schema may contain at most 1000 labels.")
    normalized = []
    seen = set()
    for item in labels:
        if isinstance(item, str):
            name = item.strip()
            if not name:
                raise PayloadValidationError("Labels must not be blank.")
            key = name.casefold()
            if key in seen:
                raise PayloadValidationError(f"Duplicate label: {name}")
            seen.add(key)
            normalized.append(name)
        elif isinstance(item, Mapping):
            name = str(item.get("name", "")).strip()
            if not name:
                raise PayloadValidationError("Label objects require a name.")
            key = name.casefold()
            if key in seen:
                raise PayloadValidationError(f"Duplicate label: {name}")
            seen.add(key)
            normalized.append(dict(item, name=name))
        else:
            raise PayloadValidationError("Each label must be text or an object.")
    return normalized
