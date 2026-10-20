"""Add immutable dataset version snapshots."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("datasets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DatasetVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version_number", models.PositiveIntegerField()),
                ("manifest", models.JSONField()),
                ("content_hash", models.CharField(db_index=True, max_length=64)),
                ("task_count", models.PositiveIntegerField(default=0)),
                ("annotation_count", models.PositiveIntegerField(default=0)),
                ("change_note", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="dataset_versions_created", to=settings.AUTH_USER_MODEL)),
                ("dataset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="datasets.dataset")),
            ],
            options={"ordering": ("-version_number",)},
        ),
        migrations.AddConstraint(
            model_name="datasetversion",
            constraint=models.UniqueConstraint(fields=("dataset", "version_number"), name="unique_dataset_version_number"),
        ),
    ]
