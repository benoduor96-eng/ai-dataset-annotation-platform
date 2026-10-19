"""Explicit API serializers with tenant-bound write validation."""
from rest_framework import serializers

from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask, Review
from apps.datasets.models import Dataset, Project
from .services.validators import PayloadValidationError, validate_schema_labels, validate_task_payload


class ProjectSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = ("id", "name", "description", "owner", "created_at", "task_count")
        read_only_fields = ("id", "owner", "created_at", "task_count")


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ("id", "project", "name", "description", "item_count", "created_at")
        read_only_fields = ("id", "item_count", "created_at")

    def validate_project(self, project):
        request = self.context.get("request")
        if request is None or project.owner_id != request.user.id:
            raise serializers.ValidationError("Choose a project you own.")
        return project


class SchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotationSchema
        fields = ("id", "dataset", "name", "label_type", "labels", "version")
        read_only_fields = ("id", "version")

    def validate_dataset(self, dataset):
        request = self.context.get("request")
        if request is None or dataset.project.owner_id != request.user.id:
            raise serializers.ValidationError("Choose a dataset in your workspace.")
        return dataset

    def validate_labels(self, labels):
        try:
            return validate_schema_labels(labels)
        except PayloadValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnotationTask
        fields = ("id", "dataset", "external_id", "payload", "assignee", "status",
                  "ai_suggestions", "created_at", "updated_at")
        read_only_fields = ("id", "assignee", "status", "created_at", "updated_at")

    def validate_dataset(self, dataset):
        request = self.context.get("request")
        if request is None or dataset.project.owner_id != request.user.id:
            raise serializers.ValidationError("Choose a dataset in your workspace.")
        return dataset

    def validate_payload(self, payload):
        try:
            return validate_task_payload(payload)
        except PayloadValidationError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Annotation
        fields = ("id", "task", "annotator", "data", "confidence", "created_at", "updated_at")
        read_only_fields = ("id", "annotator", "created_at", "updated_at")

    def validate_task(self, task):
        request = self.context.get("request")
        if request is None or task.dataset.project.owner_id != request.user.id:
            raise serializers.ValidationError("Choose a task in your workspace.")
        if task.status in ("approved", "rejected"):
            raise serializers.ValidationError("Reviewed tasks cannot be edited.")
        return task

    def validate_confidence(self, confidence):
        if confidence is not None and not 0 <= confidence <= 1:
            raise serializers.ValidationError("Confidence must be between 0 and 1.")
        return confidence


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ("id", "annotation", "reviewer", "decision", "comment", "created_at")
        read_only_fields = ("id", "reviewer", "created_at")

    def validate_annotation(self, annotation):
        request = self.context.get("request")
        if request is None or annotation.task.dataset.project.owner_id != request.user.id:
            raise serializers.ValidationError("Choose an annotation in your workspace.")
        return annotation
