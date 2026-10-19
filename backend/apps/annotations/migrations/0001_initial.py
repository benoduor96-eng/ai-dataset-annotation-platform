# Generated as the initial schema for the annotation domain.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("datasets", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AnnotationSchema",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("label_type", models.CharField(choices=[("classification", "Classification"), ("ner", "Named Entity"), ("bbox", "Bounding Box"), ("segmentation", "Segmentation")], max_length=32)),
                ("labels", models.JSONField(default=list)),
                ("version", models.PositiveIntegerField(default=1)),
                ("dataset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="schemas", to="datasets.dataset")),
            ],
        ),
        migrations.CreateModel(
            name="AnnotationTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=160, unique=True)),
                ("payload", models.JSONField(default=dict)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("submitted", "Submitted"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("ai_suggestions", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assignee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_tasks", to=settings.AUTH_USER_MODEL)),
                ("dataset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="datasets.dataset")),
            ],
        ),
        migrations.CreateModel(
            name="Annotation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.JSONField(default=dict)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("annotator", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="annotations", to="annotations.annotationtask")),
            ],
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(choices=[("approved", "Approved"), ("rejected", "Rejected")], max_length=20)),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("annotation", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="review", to="annotations.annotation")),
                ("reviewer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
