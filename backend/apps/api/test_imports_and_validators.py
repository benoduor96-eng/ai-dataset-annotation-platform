"""Service-level tests for task payload validation and atomic bulk imports."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.annotations.models import AnnotationTask, AuditEvent
from apps.datasets.models import Dataset, Project
from apps.api.services.imports import import_tasks
from apps.api.services.validators import (
    PayloadValidationError,
    validate_schema_labels,
    validate_task_payload,
)


class PayloadValidatorTests(TestCase):
    def test_task_payload_requires_a_mapping(self):
        for value in (None, [], "text", 5):
            with self.subTest(value=value), self.assertRaises(PayloadValidationError):
                validate_task_payload(value)

    def test_task_payload_rejects_empty_and_overwide_objects(self):
        with self.assertRaisesRegex(PayloadValidationError, "must not be empty"):
            validate_task_payload({})
        with self.assertRaisesRegex(PayloadValidationError, "too many"):
            validate_task_payload({str(index): index for index in range(101)})

    def test_task_payload_returns_a_copy_of_mapping(self):
        payload = {"text": "sample"}
        normalized = validate_task_payload(payload)
        self.assertEqual(normalized, payload)
        self.assertIsNot(normalized, payload)

    def test_schema_labels_normalize_strings_and_object_names(self):
        result = validate_schema_labels([" cat ", {"name": " dog ", "color": "brown"}])
        self.assertEqual(result, ["cat", {"name": "dog", "color": "brown"}])

    def test_schema_labels_reject_non_lists_and_oversized_lists(self):
        with self.assertRaisesRegex(PayloadValidationError, "must be a list"):
            validate_schema_labels("cat")
        with self.assertRaisesRegex(PayloadValidationError, "at most 1000"):
            validate_schema_labels(["label"] * 1001)

    def test_schema_labels_reject_blank_duplicate_and_invalid_items(self):
        invalid_values = [
            [""],
            ["cat", " CAT "],
            [{"name": ""}],
            [{"name": "cat"}, {"name": "CAT"}],
            [None],
        ]
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(PayloadValidationError):
                validate_schema_labels(value)


class BulkImportServiceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="import-owner", password="pass1234")
        self.project = Project.objects.create(owner=self.owner, name="Import project")
        self.dataset = Dataset.objects.create(project=self.project, name="Import dataset")

    def rows(self, count=2):
        return [
            {"external_id": f"item-{index}", "payload": {"text": f"Text {index}"}}
            for index in range(count)
        ]

    def test_import_creates_tasks_updates_count_and_records_event(self):
        created = import_tasks(dataset=self.dataset, rows=self.rows(), actor=self.owner)
        self.dataset.refresh_from_db()
        self.assertEqual(len(created), 2)
        self.assertEqual(self.dataset.item_count, 2)
        event = AuditEvent.objects.get(event_type="dataset.tasks_imported")
        self.assertEqual(event.actor, self.owner)
        self.assertEqual(event.metadata["created_count"], 2)
        self.assertEqual(AnnotationTask.objects.filter(dataset=self.dataset).count(), 2)

    def test_empty_non_list_and_oversized_batches_are_rejected(self):
        cases = [
            (None, "must be a list"),
            ([], "at least one"),
            (self.rows(3), "limit is 2"),
        ]
        for rows, message in cases:
            with self.subTest(rows=rows), self.assertRaisesRegex(PayloadValidationError, message):
                import_tasks(dataset=self.dataset, rows=rows, max_rows=2)
        self.assertEqual(AnnotationTask.objects.count(), 0)

    def test_invalid_rows_do_not_partially_write(self):
        rows = self.rows()
        rows[1] = {"external_id": "item-1", "payload": {}}
        with self.assertRaises(PayloadValidationError):
            import_tasks(dataset=self.dataset, rows=rows)
        self.assertEqual(AnnotationTask.objects.count(), 0)
        self.assertEqual(AuditEvent.objects.count(), 0)

    def test_duplicate_ids_inside_batch_are_rejected_atomically(self):
        rows = [
            {"external_id": "same", "payload": {"text": "one"}},
            {"external_id": "same", "payload": {"text": "two"}},
        ]
        with self.assertRaisesRegex(PayloadValidationError, "Duplicate external_id"):
            import_tasks(dataset=self.dataset, rows=rows)
        self.assertEqual(AnnotationTask.objects.count(), 0)

    def test_ids_already_used_by_another_dataset_are_rejected(self):
        other_dataset = Dataset.objects.create(project=self.project, name="Other dataset")
        AnnotationTask.objects.create(
            dataset=other_dataset, external_id="global-id", payload={"text": "existing"}
        )
        with self.assertRaisesRegex(PayloadValidationError, "already exist"):
            import_tasks(
                dataset=self.dataset,
                rows=[{"external_id": "global-id", "payload": {"text": "duplicate"}}],
            )
        self.assertFalse(AnnotationTask.objects.filter(dataset=self.dataset).exists())

    def test_import_rejects_missing_long_or_blank_identifiers(self):
        cases = [
            ({"payload": {"text": "x"}}, "requires external_id"),
            ({"external_id": "  ", "payload": {"text": "x"}}, "requires external_id"),
            ({"external_id": "x" * 161, "payload": {"text": "x"}}, "too long"),
            ({"external_id": "ok", "payload": []}, "must be a JSON object"),
        ]
        for row, message in cases:
            with self.subTest(row=row), self.assertRaisesRegex(PayloadValidationError, message):
                import_tasks(dataset=self.dataset, rows=[row])
        self.assertEqual(AnnotationTask.objects.count(), 0)
