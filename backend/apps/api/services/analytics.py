"""Read-only project metrics built from database aggregates."""
from django.db.models import Count, Q

from apps.annotations.models import Annotation, AnnotationTask
from apps.datasets.models import Dataset


def project_summary(project):
    """Build deterministic summary metrics for a project."""
    datasets = Dataset.objects.filter(project=project)
    tasks = AnnotationTask.objects.filter(dataset__project=project)
    task_counts = tasks.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status="pending")),
        in_progress=Count("id", filter=Q(status="in_progress")),
        submitted=Count("id", filter=Q(status="submitted")),
        approved=Count("id", filter=Q(status="approved")),
        rejected=Count("id", filter=Q(status="rejected")),
    )
    annotation_stats = Annotation.objects.filter(
        task__dataset__project=project
    ).aggregate(total=Count("id"), with_confidence=Count("id", filter=Q(confidence__isnull=False)))
    total = task_counts["total"] or 0
    reviewed = (task_counts["approved"] or 0) + (task_counts["rejected"] or 0)
    return {
        "project_id": project.pk,
        "dataset_count": datasets.count(),
        "task_count": total,
        "task_status": task_counts,
        "annotation_count": annotation_stats["total"] or 0,
        "annotations_with_confidence": annotation_stats["with_confidence"] or 0,
        "reviewed_task_count": reviewed,
        "review_coverage": round(reviewed / total, 4) if total else 0.0,
    }
