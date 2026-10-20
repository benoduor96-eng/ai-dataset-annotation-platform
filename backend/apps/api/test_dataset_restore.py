"""Regression tests for explicit, owner-scoped dataset restoration."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask, AuditEvent
from apps.datasets.models import Dataset, Project

class DatasetRestoreApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="restore-owner", password="pass1234")
        self.other = User.objects.create_user(username="restore-other", password="pass1234")
        self.project = Project.objects.create(owner=self.owner, name="Restore project")
        self.dataset = Dataset.objects.create(project=self.project, name="Original dataset")
        self.schema = AnnotationSchema.objects.create(dataset=self.dataset, name="Labels", label_type="classification", labels=["cat"])
        self.task = AnnotationTask.objects.create(dataset=self.dataset, external_id="restore-task-001", payload={"text": "before"})
        Annotation.objects.create(task=self.task, annotator=self.owner, data={"label": "cat"}, confidence=0.9)
        self.client.force_authenticate(self.owner)

    def test_restore_requires_explicit_confirmation_and_restores_snapshot(self):
        snap = self.client.post(f"/api/datasets/{self.dataset.pk}/versions/", {"change_note": "baseline"}, format="json")
        self.assertEqual(snap.status_code, 201)
        self.task.payload = {"text": "changed"}
        self.task.save()
        Annotation.objects.all().delete()
        AnnotationTask.objects.create(dataset=self.dataset, external_id="extra-task", payload={})
        missing_confirm = self.client.post(f"/api/datasets/{self.dataset.pk}/versions/1/restore/", {}, format="json")
        self.assertEqual(missing_confirm.status_code, 400)
        restored = self.client.post(f"/api/datasets/{self.dataset.pk}/versions/1/restore/", {"confirm": True}, format="json")
        self.assertEqual(restored.status_code, 200)
        self.assertEqual(restored.data["restored_task_count"], 1)
        self.assertEqual(AnnotationTask.objects.filter(dataset=self.dataset).count(), 1)
        task = AnnotationTask.objects.get(dataset=self.dataset, external_id="restore-task-001")
        self.assertEqual(task.payload, {"text": "before"})
        self.assertEqual(task.annotations.count(), 1)
        self.assertTrue(AuditEvent.objects.filter(event_type="dataset.version_restored").exists())

    def test_cannot_restore_another_owners_dataset(self):
        private_project = Project.objects.create(owner=self.other, name="Private")
        private_dataset = Dataset.objects.create(project=private_project, name="Private dataset")
        response = self.client.post(f"/api/datasets/{private_dataset.pk}/versions/1/restore/", {"confirm": True}, format="json")
        self.assertEqual(response.status_code, 404)
