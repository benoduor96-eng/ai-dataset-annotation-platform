"""Tests for project reports and HMAC-authenticated integration imports."""
import hashlib
import hmac
import json
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from apps.annotations.models import AnnotationTask
from apps.datasets.models import Dataset, Project

class IntegrationAndReportingTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="integration-owner", password="pass1234")
        self.project = Project.objects.create(owner=self.owner, name="Report project")
        self.dataset = Dataset.objects.create(project=self.project, name="Inbound dataset")
        self.client.force_authenticate(self.owner)

    def test_project_report_contains_dataset_workflow_and_version_counts(self):
        AnnotationTask.objects.create(dataset=self.dataset, external_id="report-submitted", payload={}, status="submitted")
        response = self.client.get(f"/api/projects/{self.project.pk}/report/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["datasets"][0]["dataset_name"], "Inbound dataset")
        self.assertEqual(response.data["datasets"][0]["task_status"]["submitted"], 1)
        self.assertEqual(response.data["submitted_awaiting_review"], 1)

    @override_settings()
    def test_signed_webhook_imports_tasks_without_user_jwt(self):
        payload = {"dataset_id": self.dataset.pk, "tasks": [{"external_id": "external-task-001", "payload": {"text": "hello"}}]}
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        secret = "test-webhook-secret"
        signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        self.client.force_authenticate(user=None)
        with __import__("unittest").mock.patch.dict("os.environ", {"INTEGRATION_WEBHOOK_SECRET": secret}):
            response = self.client.generic("POST", "/api/integrations/webhooks/tasks/", body, content_type="application/json", HTTP_X_PLATFORM_SIGNATURE=signature)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created"], 1)
        self.assertTrue(AnnotationTask.objects.filter(dataset=self.dataset, external_id="external-task-001").exists())

    def test_webhook_rejects_invalid_signature(self):
        self.client.force_authenticate(user=None)
        with __import__("unittest").mock.patch.dict("os.environ", {"INTEGRATION_WEBHOOK_SECRET": "correct-secret"}):
            response = self.client.generic("POST", "/api/integrations/webhooks/tasks/", b'{"dataset_id":1,"tasks":[]}', content_type="application/json", HTTP_X_PLATFORM_SIGNATURE="sha256=wrong")
        self.assertEqual(response.status_code, 401)

    def test_webhook_fails_closed_when_secret_is_missing(self):
        self.client.force_authenticate(user=None)
        with __import__("unittest").mock.patch.dict("os.environ", {}, clear=True):
            response = self.client.generic("POST", "/api/integrations/webhooks/tasks/", b'{}', content_type="application/json")
        self.assertEqual(response.status_code, 503)
