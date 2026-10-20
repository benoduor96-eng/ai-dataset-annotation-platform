"""Add project memberships and configurable quality rules."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [("datasets", "0002_datasetversion"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="ProjectMembership", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("role", models.CharField(choices=[("admin", "Administrator"), ("annotator", "Annotator"), ("reviewer", "Reviewer")], default="annotator", max_length=16)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="datasets.project")),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_memberships", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ("role", "user_id")}),
        migrations.AddConstraint(model_name="projectmembership", constraint=models.UniqueConstraint(fields=("project", "user"), name="unique_project_membership")),
        migrations.CreateModel(name="QualityRule", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=160)),
            ("rule_type", models.CharField(choices=[("min_confidence", "Minimum confidence"), ("require_non_empty", "Require non-empty annotation"), ("allowed_labels", "Restrict labels to an allow-list"), ("max_annotations", "Maximum annotations per task")], max_length=32)),
            ("parameters", models.JSONField(blank=True, default=dict)), ("enabled", models.BooleanField(default=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="quality_rules_created", to=settings.AUTH_USER_MODEL)),
            ("dataset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quality_rules", to="datasets.dataset")),
        ], options={"ordering": ("id",)}),
        migrations.AddConstraint(model_name="qualityrule", constraint=models.UniqueConstraint(fields=("dataset", "name"), name="unique_dataset_quality_rule_name")),
    ]
