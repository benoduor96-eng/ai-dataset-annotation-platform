"""Dataset-level operational reporting built from scoped ORM aggregates."""
from django.db.models import Count, Q
from apps.annotations.models import AnnotationTask
from apps.datasets.models import Dataset, DatasetVersion
from .analytics import project_summary

def build_project_report(project):
    base = project_summary(project)
    datasets = Dataset.objects.filter(project=project).order_by("id")
    dataset_rows = []
    for dataset in datasets:
        counts = AnnotationTask.objects.filter(dataset=dataset).aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            in_progress=Count("id", filter=Q(status="in_progress")),
            submitted=Count("id", filter=Q(status="submitted")),
            approved=Count("id", filter=Q(status="approved")),
            rejected=Count("id", filter=Q(status="rejected")),
        )
        dataset_rows.append({
            "dataset_id": dataset.pk,
            "dataset_name": dataset.name,
            "task_status": {key: value or 0 for key, value in counts.items()},
            "enabled_quality_rule_count": dataset.quality_rules.filter(enabled=True).count(),
            "saved_version_count": DatasetVersion.objects.filter(dataset=dataset).count(),
        })
    base["datasets"] = dataset_rows
    base["submitted_awaiting_review"] = base["task_status"].get("submitted", 0)
    return base
