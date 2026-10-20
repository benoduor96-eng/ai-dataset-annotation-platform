"""Content-addressed dataset snapshot creation.

A snapshot records schema, task payload, and annotation state as JSON. It is
immutable through the application API. Hashes are calculated from canonical
JSON so equivalent state produces the same digest independent of key order.
"""
import hashlib
import json

from django.db import transaction
from django.db.models import Max

from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask
from apps.datasets.models import Dataset, DatasetVersion
from .audit import record_event


def build_dataset_manifest(dataset):
    """Build a deterministic JSON-compatible manifest for the current dataset."""
    schemas = list(dataset.schemas.order_by("pk").values(
        "id", "name", "label_type", "labels", "version"
    ))
    tasks = []
    annotation_count = 0
    queryset = AnnotationTask.objects.filter(dataset=dataset).order_by("pk").prefetch_related("annotations")
    for task in queryset:
        annotations = []
        for annotation in task.annotations.all().order_by("pk"):
            annotations.append({
                "id": annotation.pk,
                "annotator_id": annotation.annotator_id,
                "data": annotation.data,
                "confidence": annotation.confidence,
            })
        annotation_count += len(annotations)
        tasks.append({
            "id": task.pk,
            "external_id": task.external_id,
            "payload": task.payload,
            "status": task.status,
            "assignee_id": task.assignee_id,
            "ai_suggestions": task.ai_suggestions,
            "annotations": annotations,
        })
    manifest = {
        "format_version": 1,
        "dataset": {
            "id": dataset.pk,
            "name": dataset.name,
            "description": dataset.description,
        },
        "schemas": schemas,
        "tasks": tasks,
    }
    return manifest, len(tasks), annotation_count


def canonical_manifest_hash(manifest):
    """Return a SHA-256 digest of canonical UTF-8 JSON."""
    canonical = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@transaction.atomic
def create_dataset_version(*, dataset_id, actor, change_note=""):
    """Lock a dataset, snapshot its state, and allocate the next version number."""
    dataset = Dataset.objects.select_for_update().select_related("project").get(pk=dataset_id)
    if actor is not None and dataset.project.owner_id != actor.id:
        raise PermissionError("Dataset is outside your project workspace.")
    note = str(change_note or "").strip()
    if len(note) > 500:
        raise ValueError("Change note must be 500 characters or fewer.")
    manifest, task_count, annotation_count = build_dataset_manifest(dataset)
    latest = DatasetVersion.objects.filter(dataset=dataset).aggregate(
        latest_version=Max("version_number")
    )["latest_version"] or 0
    version = DatasetVersion.objects.create(
        dataset=dataset,
        version_number=latest + 1,
        manifest=manifest,
        content_hash=canonical_manifest_hash(manifest),
        task_count=task_count,
        annotation_count=annotation_count,
        change_note=note,
        created_by=actor,
    )
    record_event(
        project=dataset.project,
        actor=actor,
        event_type="dataset.version_created",
        object_type="dataset_version",
        object_id=version.pk,
        metadata={
            "dataset_id": dataset.pk,
            "version_number": version.version_number,
            "content_hash": version.content_hash,
            "task_count": task_count,
            "annotation_count": annotation_count,
        },
    )
    return version


@transaction.atomic
def restore_dataset_version(*, dataset_id, version_number, actor):
    """Restore schemas, tasks and annotations from a saved snapshot atomically."""
    from django.contrib.auth import get_user_model

    dataset = Dataset.objects.select_for_update().select_related("project").get(pk=dataset_id)
    if actor is not None and dataset.project.owner_id != actor.id:
        raise PermissionError("Dataset is outside your project workspace.")
    version = DatasetVersion.objects.get(dataset=dataset, version_number=version_number)
    manifest = version.manifest
    if manifest.get("format_version") != 1 or not isinstance(manifest.get("tasks"), list) or not isinstance(manifest.get("schemas"), list):
        raise ValueError("Unsupported or invalid snapshot manifest.")
    User = get_user_model()
    valid_user_ids = set(User.objects.filter(pk__in=[
        value for task in manifest["tasks"]
        for value in [task.get("assignee_id")] + [
            annotation.get("annotator_id") for annotation in task.get("annotations", [])
        ]
        if value is not None
    ]).values_list("pk", flat=True))

    dataset.name = manifest.get("dataset", {}).get("name", dataset.name)
    dataset.description = manifest.get("dataset", {}).get("description", dataset.description)
    dataset.save(update_fields=["name", "description"])

    AnnotationSchema.objects.filter(dataset=dataset).delete()
    for schema in manifest["schemas"]:
        AnnotationSchema.objects.create(
            dataset=dataset,
            name=schema["name"],
            label_type=schema["label_type"],
            labels=schema.get("labels", []),
            version=schema.get("version", 1),
        )

    task_rows = manifest["tasks"]
    external_ids = [row["external_id"] for row in task_rows]
    AnnotationTask.objects.filter(dataset=dataset).exclude(external_id__in=external_ids).delete()
    restored_annotations = 0
    for row in task_rows:
        assignee_id = row.get("assignee_id")
        if assignee_id not in valid_user_ids:
            assignee_id = None
        task, _ = AnnotationTask.objects.update_or_create(
            external_id=row["external_id"],
            defaults={
                "dataset": dataset,
                "payload": row.get("payload", {}),
                "status": row.get("status", "pending"),
                "assignee_id": assignee_id,
                "ai_suggestions": row.get("ai_suggestions", []),
            },
        )
        task.annotations.all().delete()
        for item in row.get("annotations", []):
            annotator_id = item.get("annotator_id")
            if annotator_id not in valid_user_ids:
                continue
            Annotation.objects.create(
                task=task,
                annotator_id=annotator_id,
                data=item.get("data", {}),
                confidence=item.get("confidence"),
            )
            restored_annotations += 1
    record_event(
        project=dataset.project,
        actor=actor,
        event_type="dataset.version_restored",
        object_type="dataset_version",
        object_id=version.pk,
        metadata={"dataset_id": dataset.pk, "version_number": version.version_number,
                  "task_count": len(task_rows), "annotation_count": restored_annotations},
    )
    return {"dataset_id": dataset.pk, "version_number": version.version_number,
            "restored_task_count": len(task_rows), "restored_annotation_count": restored_annotations}
