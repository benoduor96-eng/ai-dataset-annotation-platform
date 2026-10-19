from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.annotations.models import AnnotationTask
from apps.datasets.models import Dataset, Project
from apps.api.services.imports import import_tasks
from apps.api.services.validators import PayloadValidationError, validate_schema_labels, validate_task_payload


class ValidationServiceTests(TestCase):
    def test_task_payload_requires_non_empty_mapping(self):
        for payload in (None, [], {}, "image"):
            with self.subTest(payload=payload):
                with self.assertRaises(PayloadValidationError):
                    validate_task_payload(payload)

    def test_task_payload_returns_mapping(self):
        payload = {"text": "sample"}
        self.assertEqual(validate_task_payload(payload), payload)

    def test_schema_labels_normalize_and_reject_duplicates_case_insensitively(self):
        self.assertEqual(validate_schema_labels([" cat ", "dog"]), ["cat", "dog"])
        with self.assertRaises(PayloadValidationError):
            validate_schema_labels(["Cat", " cat "])

    def test_schema_label_object_requires_name(self):
        with self.assertRaises(PayloadValidationError):
            validate_schema_labels([{"description": "missing name"}])


class BulkImportTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="owner", password="example")
        project = Project.objects.create(owner=user, name="Import test")
        self.dataset = Dataset.objects.create(project=project, name="Examples")

    def test_import_creates_tasks_and_updates_item_count(self):
        created = import_tasks(dataset=self.dataset, rows=[
            {"external_id": "row-1", "payload": {"text": "hello"}},
            {"external_id": "row-2", "payload": {"text": "world"}},
        ])
        self.assertEqual(len(created), 2)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.item_count, 2)
        self.assertEqual(AnnotationTask.objects.filter(dataset=self.dataset).count(), 2)

    def test_duplicate_batch_ids_fail_without_partial_writes(self):
        with self.assertRaises(PayloadValidationError):
            import_tasks(dataset=self.dataset, rows=[
                {"external_id": "same", "payload": {"text": "one"}},
                {"external_id": "same", "payload": {"text": "two"}},
            ])
        self.assertEqual(AnnotationTask.objects.count(), 0)

    def test_empty_import_fails(self):
        with self.assertRaises(PayloadValidationError):
            import_tasks(dataset=self.dataset, rows=[])
        self.assertEqual(AnnotationTask.objects.count(), 0)
