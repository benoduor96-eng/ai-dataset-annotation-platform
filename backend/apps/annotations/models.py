from django.conf import settings
from django.db import models
from apps.datasets.models import Dataset

class AnnotationSchema(models.Model):
    LABEL_TYPES=[('classification','Classification'),('ner','Named Entity'),('bbox','Bounding Box'),('segmentation','Segmentation')]
    dataset=models.ForeignKey(Dataset,on_delete=models.CASCADE,related_name='schemas')
    name=models.CharField(max_length=160)
    label_type=models.CharField(max_length=32,choices=LABEL_TYPES)
    labels=models.JSONField(default=list)
    version=models.PositiveIntegerField(default=1)

class AnnotationTask(models.Model):
    STATUS=[('pending','Pending'),('in_progress','In Progress'),('submitted','Submitted'),('approved','Approved'),('rejected','Rejected')]
    dataset=models.ForeignKey(Dataset,on_delete=models.CASCADE,related_name='tasks')
    external_id=models.CharField(max_length=160,unique=True)
    payload=models.JSONField(default=dict)
    assignee=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name='assigned_tasks')
    status=models.CharField(max_length=20,choices=STATUS,default='pending')
    ai_suggestions=models.JSONField(default=list)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class Annotation(models.Model):
    task=models.ForeignKey(AnnotationTask,on_delete=models.CASCADE,related_name='annotations')
    annotator=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    data=models.JSONField(default=dict)
    confidence=models.FloatField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class Review(models.Model):
    annotation=models.OneToOneField(Annotation,on_delete=models.CASCADE,related_name='review')
    reviewer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    decision=models.CharField(max_length=20,choices=[('approved','Approved'),('rejected','Rejected')])
    comment=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)


class AuditEvent(models.Model):
    """Append-only application event used to explain important project changes."""

    EVENT_TYPES = [
        ("task.claimed", "Task claimed"),
        ("task.submitted", "Task submitted"),
        ("task.reviewed", "Task reviewed"),
        ("annotation.created", "Annotation created"),
        ("annotation.updated", "Annotation updated"),
        ("dataset.tasks_imported", "Tasks imported"),
    ]

    project = models.ForeignKey(
        "datasets.Project",
        on_delete=models.CASCADE,
        related_name="audit_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="annotation_audit_events",
    )
    event_type = models.CharField(max_length=64, choices=EVENT_TYPES)
    object_type = models.CharField(max_length=64)
    object_id = models.CharField(max_length=128)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [
            models.Index(fields=("project", "-created_at"), name="audit_proj_created_idx"),
            models.Index(fields=("event_type", "-created_at"), name="audit_type_created_idx"),
        ]

    def __str__(self):
        return f"{self.event_type}:{self.object_type}:{self.object_id}"
