"""Bulk task import service with all-or-nothing persistence."""
from django.db import transaction

from apps.annotations.models import AnnotationTask
from .validators import PayloadValidationError, validate_task_payload


@transaction.atomic
def import_tasks(*, dataset, rows, max_rows=500):
    """Create tasks from rows shaped as {external_id, payload}.

    Duplicate IDs inside the batch and IDs already in the dataset are rejected
    before any write, so a partial import cannot leave a misleading dataset.
    """
    if not isinstance(rows, list):
        raise PayloadValidationError("Import body must be a list of task objects.")
    if not rows:
        raise PayloadValidationError("Import must contain at least one task.")
    if len(rows) > max_rows:
        raise PayloadValidationError(f"Import limit is {max_rows} tasks per request.")
    prepared = []
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise PayloadValidationError(f"Row {index} must be an object.")
        external_id = str(row.get("external_id", "")).strip()
        if not external_id:
            raise PayloadValidationError(f"Row {index} requires external_id.")
        if len(external_id) > 160:
            raise PayloadValidationError(f"Row {index} external_id is too long.")
        if external_id in seen:
            raise PayloadValidationError(f"Duplicate external_id in batch: {external_id}")
        seen.add(external_id)
        prepared.append((external_id, validate_task_payload(row.get("payload"))))
    existing = set(AnnotationTask.objects.filter(
        external_id__in=seen
    ).values_list("external_id", flat=True))
    if existing:
        raise PayloadValidationError(
            "These external IDs already exist: " + ", ".join(sorted(existing))
        )
    created = AnnotationTask.objects.bulk_create([
        AnnotationTask(dataset=dataset, external_id=external_id, payload=payload)
        for external_id, payload in prepared
    ])
    dataset.item_count = AnnotationTask.objects.filter(dataset=dataset).count()
    dataset.save(update_fields=("item_count",))
    return created
