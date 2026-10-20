"""Tests for immutable dataset snapshots and owner-scoped version history."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.annotations.models import Annotation, AnnotationTask, AuditEvent
from apps.datasets.models import Dataset, DatasetVersion, Project


class DatasetVersionApiTest(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="version-owner", password="pass1234")
        self.other = user_model.objects.create_user(username="version-other", password="pass1234")
        self.project = Project.objects.create(owner=self.owner, name="Versioned project")
        self.dataset = Dataset.objects.create(project=self.project, name="Versioned dataset")
        self.task = AnnotationTask.objects.create(
            dataset=self.dataset,
            external_id="version-task-001",
            payload={"text": "A sample"},
        )
        self.client.force_authenticate(self.owner)

    def test_create_version_snapshots_task_state_and_emits_audit_event(self):
        response = self.client.post(
            f"/api/datasets/{self.dataset.pk}/versions/",
            {"change_note": "Initial baseline"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["version_number"], 1)
        self.assertEqual(response.data["task_count"], 1)
        self.assertEqual(response.data["annotation_count"], 0)
        self.assertEqual(response.data["manifest"]["tasks"][0]["external_id"], "version-task-001")
        self.assertEqual(len(response.data["content_hash"]), 64)
        event = AuditEvent.objects.get(event_type="dataset.version_created")
        self.assertEqual(event.actor, self.owner)
        self.assertEqual(event.metadata["version_number"], 1)

    def test_version_hash_changes_when_annotation_state_changes(self):
        first = self.client.post(
            f"/api/datasets/{self.dataset.pk}/versions/", {"change_note": "Before labeling"}, format="json"
        )
        Annotation.objects.create(task=self.task, annotator=self.owner, data={"label": "cat"}, confidence=0.8)
        second = self.client.post(
            f"/api/datasets/{self.dataset.pk}/versions/", {"change_note": "After labeling"}, format="json"
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(second.data["version_number"], 2)
        self.assertEqual(second.data["annotation_count"], 1)
        self.assertNotEqual(first.data["content_hash"], second.data["content_hash"])

    def test_same_state_has_same_content_hash(self):
        first = self.client.post(f"/api/datasets/{self.dataset.pk}/versions/", {}, format="json")
        second = self.client.post(f"/api/datasets/{self.dataset.pk}/versions/", {}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.data["content_hash"], second.data["content_hash"])
        self.assertEqual(DatasetVersion.objects.filter(dataset=self.dataset).count(), 2)

    def test_version_history_is_listed_newest_first(self):
        self.client.post(f"/api/datasets/{self.dataset.pk}/versions/", {}, format="json")
        self.client.post(f"/api/datasets/{self.dataset.pk}/versions/", {"change_note": "Second"}, format="json")
        response = self.client.get(f"/api/datasets/{self.dataset.pk}/versions/")
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual([row["version_number"] for row in results], [2, 1])

    def test_cannot_create_version_for_another_users_dataset(self):
        private_project = Project.objects.create(owner=self.other, name="Private")
        private_dataset = Dataset.objects.create(project=private_project, name="Private dataset")
        response = self.client.post(f"/api/datasets/{private_dataset.pk}/versions/", {}, format="json")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(DatasetVersion.objects.filter(dataset=private_dataset).exists())

    def test_change_note_length_is_validated(self):
        response = self.client.post(
            f"/api/datasets/{self.dataset.pk}/versions/",
            {"change_note": "x" * 501},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(DatasetVersion.objects.filter(dataset=self.dataset).exists())

    def test_version_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/datasets/{self.dataset.pk}/versions/")
        self.assertEqual(response.status_code, 401)
