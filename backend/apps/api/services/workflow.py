"""Transactional annotation-task workflow operations."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.annotations.models import Annotation, AnnotationTask, Review
from .audit import record_event


class WorkflowError(Exception):
    """Raised when a task cannot make the requested state transition."""


@transaction.atomic
def claim_task(*, task_id, user):
    """Assign a pending task to a user, or return their already claimed task."""
    task = AnnotationTask.objects.select_for_update().select_related(
        "dataset__project"
    ).get(pk=task_id)
    if task.dataset.project.owner_id != user.id:
        raise WorkflowError("Task is outside your project workspace.")
    if task.assignee_id not in (None, user.id):
        raise WorkflowError("Task is already assigned to another annotator.")
    if task.status not in ("pending", "in_progress"):
        raise WorkflowError("Only pending or in-progress tasks can be claimed.")
    task.assignee = user
    task.status = "in_progress"
    task.save(update_fields=("assignee", "status", "updated_at"))
    record_event(
        project=task.dataset.project,
        actor=user,
        event_type="task.claimed",
        object_type="task",
        object_id=task.pk,
        metadata={"status": task.status},
    )
    return task


@transaction.atomic
def submit_task(*, task_id, user):
    """Submit a task only after at least one annotation has been saved."""
    task = AnnotationTask.objects.select_for_update().select_related(
        "dataset__project"
    ).get(pk=task_id)
    if task.dataset.project.owner_id != user.id:
        raise WorkflowError("Task is outside your project workspace.")
    if task.assignee_id not in (None, user.id):
        raise WorkflowError("Only the assigned annotator may submit this task.")
    if task.status not in ("pending", "in_progress"):
        raise WorkflowError("Task is not in a submittable state.")
    if not Annotation.objects.filter(task=task).exists():
        raise WorkflowError("Add at least one annotation before submitting.")
    task.status = "submitted"
    task.assignee = task.assignee or user
    task.save(update_fields=("status", "assignee", "updated_at"))
    record_event(
        project=task.dataset.project,
        actor=user,
        event_type="task.submitted",
        object_type="task",
        object_id=task.pk,
        metadata={"annotation_count": task.annotations.count(), "status": task.status},
    )
    return task


@transaction.atomic
def review_task(*, task_id, reviewer, decision, comment=""):
    """Record a review for each annotation and transition the task atomically."""
    if decision not in ("approved", "rejected"):
        raise WorkflowError("Decision must be 'approved' or 'rejected'.")
    task = AnnotationTask.objects.select_for_update().select_related(
        "dataset__project"
    ).get(pk=task_id)
    if task.dataset.project.owner_id != reviewer.id:
        raise WorkflowError("Task is outside your project workspace.")
    if task.status != "submitted":
        raise WorkflowError("Only submitted tasks can be reviewed.")
    annotations = list(Annotation.objects.select_for_update().filter(task=task))
    if not annotations:
        raise WorkflowError("Cannot review a task with no annotations.")
    for annotation in annotations:
        Review.objects.update_or_create(
            annotation=annotation,
            defaults={
                "reviewer": reviewer,
                "decision": decision,
                "comment": comment,
            },
        )
    task.status = decision
    task.save(update_fields=("status", "updated_at"))
    record_event(
        project=task.dataset.project,
        actor=reviewer,
        event_type="task.reviewed",
        object_type="task",
        object_id=task.pk,
        metadata={"decision": decision, "annotation_count": len(annotations)},
    )
    return task


def transition_history(task):
    """Return a stable, timestamp-ordered view of saved review decisions."""
    reviews = Review.objects.filter(annotation__task=task).select_related(
        "reviewer", "annotation"
    ).order_by("created_at", "pk")
    return [
        {
            "annotation_id": review.annotation_id,
            "reviewer_id": review.reviewer_id,
            "decision": review.decision,
            "comment": review.comment,
            "created_at": review.created_at.isoformat(),
        }
        for review in reviews
    ]
