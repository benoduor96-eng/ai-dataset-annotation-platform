"""Tests for schema-aware annotation quality checks and their API exposure."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask
from apps.datasets.models import Dataset, Project
from .services.quality_control import validate_annotation_data


class SchemaQualityServiceTest(APITestCase):
    def setUp(self):
        self.schema = AnnotationSchema(name="Animals", label_type="classification", labels=["cat", "dog"])

    def codes(self, data, schema=None, payload=None):
        return {issue["code"] for issue in validate_annotation_data(
            data=data, schema=schema or self.schema, task_payload=payload
        )}

    def test_classification_accepts_known_label_case_insensitively(self):
        self.assertEqual(self.codes({"label": "CAT"}), set())

    def test_classification_rejects_unknown_and_blank_labels(self):
        self.assertEqual(self.codes({"label": "wolf"}), {"unknown_label"})
        self.assertEqual(self.codes({"label": " "}), {"label_required"})

    def test_non_object_annotation_is_rejected(self):
        self.assertEqual(self.codes(["cat"]), {"annotation_object_required"})

    def test_empty_schema_allows_non_empty_class_labels(self):
        self.schema.labels = []
        self.assertEqual(self.codes({"label": "unlisted-but-valid"}), set())

    def test_ner_checks_spans_against_source_text(self):
        self.schema.label_type = "ner"
        self.schema.labels = ["PERSON"]
        payload = {"text": "Ada Lovelace"}
        self.assertEqual(self.codes(
            {"entities": [{"start": 0, "end": 3, "text": "Ada", "label": "PERSON"}]}, payload=payload
        ), set())
        self.assertEqual(self.codes(
            {"entities": [{"start": -1, "end": 20, "label": "PERSON"}]}, payload=payload
        ), {"span_out_of_range"})

    def test_bbox_requires_finite_ordered_coordinates(self):
        self.schema.label_type = "bbox"
        self.schema.labels = ["car"]
        valid = {"boxes": [{"x_min": 1, "y_min": 2, "x_max": 8, "y_max": 9, "label": "car"}]}
        self.assertEqual(self.codes(valid), set())
        invalid = {"boxes": [{"x_min": 8, "y_min": 2, "x_max": 1, "y_max": 9, "label": "car"}]}
        self.assertEqual(self.codes(invalid), {"box_dimensions_invalid"})

    def test_segmentation_requires_three_valid_points(self):
        self.schema.label_type = "segmentation"
        self.schema.labels = ["road"]
        too_small = {"segments": [{"label": "road", "points": [[0, 0], [1, 1]]}]}
        self.assertEqual(self.codes(too_small), {"polygon_points_required"})
        malformed = {"segments": [{"label": "road", "points": [[0, 0], [1, 0], ["x", 1]]}]}
        self.assertEqual(self.codes(malformed), {"point_coordinates_invalid"})


class TaskQualityCheckApiTest(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="quality-owner", password="pass1234")
        self.other_user = user_model.objects.create_user(username="quality-other", password="pass1234")
        self.client.force_authenticate(self.user)
        self.project = Project.objects.create(owner=self.user, name="Quality project")
        self.dataset = Dataset.objects.create(project=self.project, name="Images")
        self.schema = AnnotationSchema.objects.create(
            dataset=self.dataset, name="Labels", label_type="classification", labels=["cat", "dog"]
        )
        self.task = AnnotationTask.objects.create(
            dataset=self.dataset, external_id="quality-001", payload={"image_url": "https://example.test/image.jpg"}
        )

    def test_quality_check_reports_valid_and_invalid_annotations(self):
        Annotation.objects.create(task=self.task, annotator=self.user, data={"label": "cat"})
        Annotation.objects.create(task=self.task, annotator=self.user, data={"label": "wolf"})
        response = self.client.post(
            f"/api/tasks/{self.task.pk}/quality-check/", {"schema_id": self.schema.pk}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["annotation_count"], 2)
        self.assertEqual(response.data["valid_count"], 1)
        self.assertEqual(response.data["invalid_count"], 1)
        self.assertEqual(response.data["validity_rate"], 0.5)

    def test_quality_check_requires_schema_for_dataset(self):
        response = self.client.post(f"/api/tasks/{self.task.pk}/quality-check/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_quality_check_rejects_non_integer_schema_id(self):
        response = self.client.post(
            f"/api/tasks/{self.task.pk}/quality-check/", {"schema_id": "not-an-id"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_quality_check_does_not_disclose_another_users_task(self):
        other_project = Project.objects.create(owner=self.other_user, name="Private")
        other_dataset = Dataset.objects.create(project=other_project, name="Private data")
        other_task = AnnotationTask.objects.create(
            dataset=other_dataset, external_id="private-001", payload={"text": "private"}
        )
        response = self.client.post(f"/api/tasks/{other_task.pk}/quality-check/", {}, format="json")
        self.assertEqual(response.status_code, 404)
