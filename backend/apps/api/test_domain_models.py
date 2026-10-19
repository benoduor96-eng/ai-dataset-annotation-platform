from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask
from apps.datasets.models import Dataset, Project


class AnnotationDomainModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="dataset-owner",
            password="test-only-password",
        )
        self.annotator = user_model.objects.create_user(
            username="task-annotator",
            password="test-only-password",
        )
        self.project = Project.objects.create(
            owner=self.owner,
            name="Wildlife images",
        )
        self.dataset = Dataset.objects.create(
            project=self.project,
            name="Training split",
        )

    def test_task_defaults_to_pending_and_preserves_json_payload(self):
        payload = {"image_url": "https://example.invalid/sample.jpg", "source": "fixture"}
        task = AnnotationTask.objects.create(
            dataset=self.dataset,
            external_id="wildlife-0001",
            payload=payload,
        )

        self.assertEqual(task.status, "pending")
        self.assertEqual(task.payload, payload)
        self.assertEqual(task.dataset.project.owner, self.owner)

    def test_schema_keeps_label_type_and_version(self):
        schema = AnnotationSchema.objects.create(
            dataset=self.dataset,
            name="Species",
            label_type="classification",
            labels=["cat", "dog"],
            version=2,
        )

        self.assertEqual(schema.dataset, self.dataset)
        self.assertEqual(schema.label_type, "classification")
        self.assertEqual(schema.labels, ["cat", "dog"])
        self.assertEqual(schema.version, 2)

    def test_annotation_is_attributed_to_annotator_and_task(self):
        task = AnnotationTask.objects.create(
            dataset=self.dataset,
            external_id="wildlife-0002",
            payload={"text": "a dog in a field"},
            assignee=self.annotator,
        )
        annotation = Annotation.objects.create(
            task=task,
            annotator=self.annotator,
            data={"label": "dog"},
            confidence=0.9,
        )

        self.assertEqual(annotation.task, task)
        self.assertEqual(annotation.annotator, self.annotator)
        self.assertEqual(annotation.data, {"label": "dog"})
        self.assertAlmostEqual(annotation.confidence, 0.9)
