"""Regression tests for project audit-event capture and tenant-scoped reads."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.annotations.models import Annotation, AnnotationTask, AuditEvent
from apps.datasets.models import Dataset, Project


class AuditTrailApiTest(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="audit-owner", password="pass1234")
        self.other = user_model.objects.create_user(username="audit-other", password="pass1234")
        self.project = Project.objects.create(owner=self.owner, name="Audit project")
        self.dataset = Dataset.objects.create(project=self.project, name="Audit dataset")
        self.task = AnnotationTask.objects.create(
            dataset=self.dataset,
            external_id="audit-task-001",
            payload={"text": "hello world"},
        )
        self.client.force_authenticate(self.owner)

    def test_task_claim_creates_audit_event(self):
        response = self.client.post(f"/api/tasks/{self.task.pk}/claim/", {}, format="json")
        self.assertEqual(response.status_code, 200)
        event = AuditEvent.objects.get(event_type="task.claimed", object_id=str(self.task.pk))
        self.assertEqual(event.project, self.project)
        self.assertEqual(event.actor, self.owner)
        self.assertEqual(event.metadata["status"], "in_progress")

    def test_annotation_create_creates_audit_event_without_copying_annotation_data(self):
        response = self.client.post(
            "/api/annotations/",
            {"task": self.task.pk, "data": {"label": "cat"}, "confidence": 0.9},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        event = AuditEvent.objects.get(event_type="annotation.created")
        self.assertEqual(event.actor, self.owner)
        self.assertEqual(event.metadata, {"task_id": self.task.pk})
        self.assertNotIn("label", event.metadata)

    def test_audit_endpoint_only_lists_events_for_owned_projects(self):
        own = AuditEvent.objects.create(
            project=self.project,
            actor=self.owner,
            event_type="task.claimed",
            object_type="task",
            object_id=str(self.task.pk),
            metadata={"status": "in_progress"},
        )
        private_project = Project.objects.create(owner=self.other, name="Private audit project")
        AuditEvent.objects.create(
            project=private_project,
            actor=self.other,
            event_type="task.claimed",
            object_type="task",
            object_id="private-task",
            metadata={},
        )

        response = self.client.get("/api/audit-events/")
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual([row["id"] for row in results], [own.pk])

    def test_audit_endpoint_supports_event_type_filter(self):
        AuditEvent.objects.create(
            project=self.project,
            actor=self.owner,
            event_type="task.claimed",
            object_type="task",
            object_id=str(self.task.pk),
            metadata={},
        )
        AuditEvent.objects.create(
            project=self.project,
            actor=self.owner,
            event_type="annotation.created",
            object_type="annotation",
            object_id="42",
            metadata={},
        )
        response = self.client.get("/api/audit-events/?event_type=task.claimed")
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertTrue(results)
        self.assertTrue(all(row["event_type"] == "task.claimed" for row in results))

    def test_audit_endpoint_is_read_only(self):
        response = self.client.post("/api/audit-events/", {}, format="json")
        self.assertEqual(response.status_code, 405)

    def test_audit_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/audit-events/")
        self.assertEqual(response.status_code, 401)
