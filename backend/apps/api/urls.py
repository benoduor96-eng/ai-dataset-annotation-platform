from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnnotationViewSet, AuditEventViewSet, DatasetViewSet, ProjectViewSet, ReviewViewSet, SchemaViewSet,
    TaskViewSet, dataset_import, integration_tasks_webhook, project_export,
)

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="projects")
router.register("datasets", DatasetViewSet, basename="datasets")
router.register("schemas", SchemaViewSet, basename="schemas")
router.register("tasks", TaskViewSet, basename="tasks")
router.register("annotations", AnnotationViewSet, basename="annotations")
router.register("audit-events", AuditEventViewSet, basename="audit-events")
router.register("reviews", ReviewViewSet, basename="reviews")

urlpatterns = [
    path("", include(router.urls)),
    path("datasets/<int:pk>/import/", dataset_import, name="dataset-import"),
    path("projects/<int:pk>/export/", project_export, name="project-export"),
    path("integrations/webhooks/tasks/", integration_tasks_webhook, name="integration-tasks-webhook"),
]
