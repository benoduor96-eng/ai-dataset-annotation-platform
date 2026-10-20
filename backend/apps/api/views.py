"""REST endpoints for project, dataset, annotation and review workflows."""
import json

from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from rest_framework import decorators, response, status, viewsets
from rest_framework.exceptions import ValidationError

from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask, Review
from apps.datasets.models import Dataset, Project
from .serializers import (
    AnnotationSerializer, DatasetSerializer, ProjectSerializer, ReviewSerializer,
    SchemaSerializer, TaskSerializer,
)
from .services.analytics import project_summary
from .services.imports import import_tasks
from .services.quality_control import build_quality_report
from .services.validators import PayloadValidationError
from .services.workflow import WorkflowError, claim_task, review_task, submit_task


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


class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class = DatasetSerializer

    def get_queryset(self):
        return Dataset.objects.filter(project__owner=self.request.user)


class SchemaViewSet(viewsets.ModelViewSet):
    serializer_class = SchemaSerializer

    def get_queryset(self):
        return AnnotationSchema.objects.filter(dataset__project__owner=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return AnnotationTask.objects.filter(dataset__project__owner=self.request.user)

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
        schema = schemas.filter(pk=schema_id).first() if schema_id else schemas.first()
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
        return response.Response(report)


class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        return Annotation.objects.filter(task__dataset__project__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(annotator=self.request.user)


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
        created = import_tasks(dataset=dataset, rows=request.data.get("tasks"))
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
