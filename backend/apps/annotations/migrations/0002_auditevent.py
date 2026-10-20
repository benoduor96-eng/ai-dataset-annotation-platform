"""Create the append-only audit event table."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("annotations", "0001_initial"),
        ("datasets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(choices=[
                    ("task.claimed", "Task claimed"),
                    ("task.submitted", "Task submitted"),
                    ("task.reviewed", "Task reviewed"),
                    ("annotation.created", "Annotation created"),
                    ("annotation.updated", "Annotation updated"),
                    ("dataset.tasks_imported", "Tasks imported"),
                    ("dataset.version_created", "Dataset version created"),
                ], max_length=64)),
                ("object_type", models.CharField(max_length=64)),
                ("object_id", models.CharField(max_length=128)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="annotation_audit_events", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="datasets.project")),
            ],
            options={
                "ordering": ("-created_at", "-pk"),
                "indexes": [
                    models.Index(fields=["project", "-created_at"], name="audit_proj_created_idx"),
                    models.Index(fields=["event_type", "-created_at"], name="audit_type_created_idx"),
                ],
            },
        ),
    ]
