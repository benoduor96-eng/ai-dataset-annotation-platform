"""REST endpoints for project, dataset, annotation and review workflows."""
import hashlib
import hmac
import json
import os

from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny

from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask, AuditEvent, Review
from apps.datasets.models import Dataset, DatasetVersion, Project, ProjectMembership, QualityRule
from .serializers import (
    AnnotationSerializer, AuditEventSerializer, DatasetSerializer, DatasetVersionSerializer, ProjectMembershipSerializer, ProjectSerializer, QualityRuleSerializer, ReviewSerializer,
    SchemaSerializer, TaskSerializer,
)
from .services.analytics import project_summary
from .services.audit import record_event
from .services.imports import import_tasks
from .services.quality_control import build_quality_report
from .services.reporting import build_project_report
from .services.configurable_quality import apply_quality_rules
from .services.validators import PayloadValidationError
from .services.workflow import WorkflowError, claim_task, review_task, submit_task
from .services.versioning import create_dataset_version, restore_dataset_version


def health(request):
    return JsonResponse({"status": "ok", "service": "django-platform"})


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user).annotate(
            task_count=Count("datasets__tasks", distinct=True)
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @decorators.action(detail=True, methods=["get"])
    def metrics(self, request, pk=None):
        return response.Response(project_summary(self.get_object()))

    @decorators.action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        """Return a detailed, read-only project operations report."""
        return response.Response(build_project_report(self.get_object()))

    @decorators.action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        project = self.get_object()
        if request.method == "GET":
            qs = ProjectMembership.objects.filter(project=project).select_related("user")
            return response.Response(ProjectMembershipSerializer(qs, many=True).data)
        from django.contrib.auth import get_user_model
        user_id, role = request.data.get("user_id"), request.data.get("role", "annotator")
        if role not in {"admin", "annotator", "reviewer"}:
            return response.Response({"role": "Choose admin, annotator, or reviewer."}, status=400)
        try:
            user = get_user_model().objects.get(pk=user_id)
        except (TypeError, ValueError, get_user_model().DoesNotExist):
            return response.Response({"user_id": "User does not exist."}, status=400)
        if user.pk == project.owner_id:
            return response.Response({"user_id": "The owner does not need a membership record."}, status=400)
        member, created = ProjectMembership.objects.update_or_create(project=project, user=user, defaults={"role": role})
        return response.Response(ProjectMembershipSerializer(member).data, status=201 if created else 200)

    @decorators.action(detail=True, methods=["delete"], url_path=r"members/(?P<user_id>[^/.]+)")
    def remove_member(self, request, pk=None, user_id=None):
        project = self.get_object()
        deleted, _ = ProjectMembership.objects.filter(project=project, user_id=user_id).delete()
        return response.Response(status=204) if deleted else response.Response({"detail": "Member not found."}, status=404)


class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = DatasetSerializer

    def get_queryset(self):
        return Dataset.objects.filter(project__owner=self.request.user)

    @decorators.action(detail=True, methods=["get", "post"], url_path="quality-rules")
    def quality_rules(self, request, pk=None):
        dataset = self.get_object()
        if request.method == "GET":
            return response.Response(QualityRuleSerializer(dataset.quality_rules.all(), many=True).data)
        serializer = QualityRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule = serializer.save(dataset=dataset, created_by=request.user)
        return response.Response(QualityRuleSerializer(rule).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=["post"], url_path=r"versions/(?P<version_number>[^/.]+)/restore")
    def restore_version(self, request, pk=None, version_number=None):
        dataset = self.get_object()
        if request.data.get("confirm") is not True:
            return response.Response({"confirm": "Set confirm=true to replace the dataset with this snapshot."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = restore_dataset_version(dataset_id=dataset.pk, version_number=version_number, actor=request.user)
        except DatasetVersion.DoesNotExist:
            return response.Response({"detail": "Version not found."}, status=status.HTTP_404_NOT_FOUND)
        return response.Response(result)

    @decorators.action(detail=True, methods=["get", "post"], url_path="versions")
    def versions(self, request, pk=None):
        """List immutable snapshots or create a new snapshot of the current state."""
        dataset = self.get_object()
        if request.method == "GET":
            versions = DatasetVersion.objects.filter(dataset=dataset).select_related("created_by")
            page = self.paginate_queryset(versions)
            serializer = DatasetVersionSerializer(page if page is not None else versions, many=True)
            return self.get_paginated_response(serializer.data) if page is not None else response.Response(serializer.data)

        note = request.data.get("change_note", "")
        if not isinstance(note, str):
            return response.Response(
                {"change_note": "Must be a string."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            version = create_dataset_version(
                dataset_id=dataset.pk,
                actor=request.user,
                change_note=note,
            )
        except ValueError as exc:
            return response.Response({"change_note": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(
            DatasetVersionSerializer(version).data,
            status=status.HTTP_201_CREATED,
        )


class SchemaViewSet(viewsets.ModelViewSet):
    serializer_class = SchemaSerializer

    def get_queryset(self):
        return AnnotationSchema.objects.filter(dataset__project__owner=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return AnnotationTask.objects.filter(dataset__project__owner=self.request.user)

    @decorators.action(detail=False, methods=["get"], url_path="review-queue")
    def review_queue(self, request):
        queryset = self.get_queryset().filter(status="submitted").order_by("updated_at", "pk")
        dataset_id = request.query_params.get("dataset_id")
        if dataset_id:
            try:
                queryset = queryset.filter(dataset_id=int(dataset_id))
            except (TypeError, ValueError):
                return response.Response({"dataset_id": "Must be an integer."}, status=400)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else response.Response(serializer.data)

    @decorators.action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        try:
            task = claim_task(task_id=self.get_object().pk, user=request.user)
        except WorkflowError as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(self.get_serializer(task).data)

    @decorators.action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        try:
            task = submit_task(task_id=self.get_object().pk, user=request.user)
        except WorkflowError as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(self.get_serializer(task).data)

    @decorators.action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        try:
            task = review_task(
                task_id=self.get_object().pk,
                reviewer=request.user,
                decision=request.data.get("decision"),
                comment=str(request.data.get("comment", ""))[:5000],
            )
        except WorkflowError as exc:
            return response.Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return response.Response(self.get_serializer(task).data)

    @decorators.action(detail=True, methods=["post"], url_path="quality-check")
    def quality_check(self, request, pk=None):
        """Report schema validation for a task's annotations without mutating them."""
        task = self.get_object()
        schemas = AnnotationSchema.objects.filter(dataset=task.dataset).order_by("pk")
        schema_id = request.data.get("schema_id")
        if schema_id not in (None, ""):
            try:
                schema_id = int(schema_id)
            except (TypeError, ValueError):
                return response.Response(
                    {"detail": "schema_id must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            schema = schemas.filter(pk=schema_id).first()
        else:
            schema = schemas.first()
        if schema is None:
            return response.Response(
                {"detail": "Provide a schema_id belonging to this task's dataset, or create a schema first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        annotations = list(task.annotations.select_related("annotator").order_by("pk"))
        report = build_quality_report(
            annotations=annotations,
            schema=schema,
            task_payload=task.payload,
        )
        rules = task.dataset.quality_rules.filter(enabled=True).order_by("pk")
        return response.Response(apply_quality_rules(report, annotations, rules))


class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        return Annotation.objects.filter(task__dataset__project__owner=self.request.user)

    def perform_create(self, serializer):
        annotation = serializer.save(annotator=self.request.user)
        record_event(
            project=annotation.task.dataset.project,
            actor=self.request.user,
            event_type="annotation.created",
            object_type="annotation",
            object_id=annotation.pk,
            metadata={"task_id": annotation.task_id},
        )

    def perform_update(self, serializer):
        annotation = serializer.save()
        record_event(
            project=annotation.task.dataset.project,
            actor=self.request.user,
            event_type="annotation.updated",
            object_type="annotation",
            object_id=annotation.pk,
            metadata={"task_id": annotation.task_id},
        )


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only, owner-scoped audit history with optional query filters."""

    serializer_class = AuditEventSerializer

    def get_queryset(self):
        queryset = AuditEvent.objects.filter(
            project__owner=self.request.user
        ).select_related("project", "actor")
        event_type = self.request.query_params.get("event_type")
        object_type = self.request.query_params.get("object_type")
        object_id = self.request.query_params.get("object_id")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if object_type:
            queryset = queryset.filter(object_type=object_type)
        if object_id:
            queryset = queryset.filter(object_id=object_id)
        return queryset


class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        return Review.objects.filter(annotation__task__dataset__project__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


@decorators.api_view(["post"])
def dataset_import(request, pk):
    dataset = Dataset.objects.filter(pk=pk, project__owner=request.user).first()
    if dataset is None:
        return response.Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    try:
        created = import_tasks(dataset=dataset, rows=request.data.get("tasks"), actor=request.user)
    except PayloadValidationError as exc:
        raise ValidationError({"tasks": str(exc)}) from exc
    return response.Response(
        {"created": len(created), "task_ids": [task.pk for task in created]},
        status=status.HTTP_201_CREATED,
    )


@decorators.api_view(["get"])
def project_export(request, pk):
    project = Project.objects.filter(pk=pk, owner=request.user).first()
    if project is None:
        return response.Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
    rows = []
    tasks = AnnotationTask.objects.filter(
        dataset__project=project
    ).select_related("dataset").prefetch_related("annotations")
    for task in tasks:
        for annotation in task.annotations.all():
            rows.append({
                "task_id": task.external_id,
                "dataset": task.dataset.name,
                "payload": task.payload,
                "annotation": annotation.data,
                "confidence": annotation.confidence,
                "annotator_id": annotation.annotator_id,
                "created_at": annotation.created_at.isoformat(),
            })
    return HttpResponse(
        json.dumps(rows, indent=2, ensure_ascii=False),
        content_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="project-{pk}.json"'},
    )


@decorators.api_view(["post"])
@decorators.permission_classes([AllowAny])
def integration_tasks_webhook(request):
    """Accept signed task imports from trusted external annotation systems.

    Configure INTEGRATION_WEBHOOK_SECRET in the server environment. Signature
    format: X-Platform-Signature: sha256=<hex HMAC of the exact raw request body>.
    """
    secret = os.getenv("INTEGRATION_WEBHOOK_SECRET", "")
    if not secret:
        return response.Response({"detail": "Webhook integration is not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    supplied = request.headers.get("X-Platform-Signature", "")
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), request.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied, expected):
        return response.Response({"detail": "Invalid webhook signature."}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return response.Response({"detail": "Request body must be valid JSON."}, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(payload, dict):
        return response.Response({"detail": "Request body must be a JSON object."}, status=status.HTTP_400_BAD_REQUEST)
    dataset_id, tasks = payload.get("dataset_id"), payload.get("tasks")
    if isinstance(dataset_id, bool) or not isinstance(dataset_id, int) or dataset_id < 1:
        return response.Response({"dataset_id": "Must be a positive integer."}, status=status.HTTP_400_BAD_REQUEST)
    dataset = Dataset.objects.filter(pk=dataset_id).select_related("project").first()
    if dataset is None:
        return response.Response({"detail": "Dataset not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        created = import_tasks(dataset=dataset, rows=tasks, actor=None)
    except PayloadValidationError as exc:
        return response.Response({"tasks": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return response.Response({"created": len(created), "task_ids": [task.pk for task in created]}, status=status.HTTP_201_CREATED)
