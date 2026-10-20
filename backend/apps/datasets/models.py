from django.conf import settings
from django.db import models

class Project(models.Model):
    name=models.CharField(max_length=160)
    description=models.TextField(blank=True)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='projects')
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Dataset(models.Model):
    project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name='datasets')
    name=models.CharField(max_length=160)
    description=models.TextField(blank=True)
    item_count=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name


class DatasetVersion(models.Model):
    """Immutable, content-addressed snapshot of a dataset's annotation state."""

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    manifest = models.JSONField()
    content_hash = models.CharField(max_length=64, db_index=True)
    task_count = models.PositiveIntegerField(default=0)
    annotation_count = models.PositiveIntegerField(default=0)
    change_note = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dataset_versions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-version_number",)
        constraints = [
            models.UniqueConstraint(
                fields=("dataset", "version_number"),
                name="unique_dataset_version_number",
            ),
        ]

    def __str__(self):
        return f"{self.dataset.name} v{self.version_number}"


class ProjectMembership(models.Model):
    ROLE_CHOICES = [("admin", "Administrator"), ("annotator", "Annotator"), ("reviewer", "Reviewer")]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="project_memberships")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="annotator")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("role", "user_id")
        constraints = [models.UniqueConstraint(fields=("project", "user"), name="unique_project_membership")]


class QualityRule(models.Model):
    RULE_TYPES = [("min_confidence", "Minimum confidence"), ("require_non_empty", "Require non-empty annotation"), ("allowed_labels", "Restrict labels to an allow-list"), ("max_annotations", "Maximum annotations per task")]
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="quality_rules")
    name = models.CharField(max_length=160)
    rule_type = models.CharField(max_length=32, choices=RULE_TYPES)
    parameters = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="quality_rules_created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("id",)
        constraints = [models.UniqueConstraint(fields=("dataset", "name"), name="unique_dataset_quality_rule_name")]
