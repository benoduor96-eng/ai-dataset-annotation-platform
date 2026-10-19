from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.annotations.models import Annotation, AnnotationTask
from apps.datasets.models import Dataset, Project
from apps.api.services.quality import project_agreement


class ProjectAgreementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(username="quality-owner", password="test-password")
        self.annotator_a = user_model.objects.create_user(username="quality-a", password="test-password")
        self.annotator_b = user_model.objects.create_user(username="quality-b", password="test-password")
        self.annotator_c = user_model.objects.create_user(username="quality-c", password="test-password")
        self.project = Project.objects.create(owner=self.owner, name="Agreement project")
        self.dataset = Dataset.objects.create(project=self.project, name="Agreement dataset")

    def make_task(self, external_id):
        return AnnotationTask.objects.create(
            dataset=self.dataset, external_id=external_id, payload={"text": external_id}
        )

    def annotate(self, task, user, data):
        return Annotation.objects.create(task=task, annotator=user, data=data)

    def test_exact_match_agreement_compares_different_annotators(self):
        matching_task = self.make_task("match")
        self.annotate(matching_task, self.annotator_a, {"label": "cat"})
        self.annotate(matching_task, self.annotator_b, {"label": "cat"})

        disagreement_task = self.make_task("disagreement")
        self.annotate(disagreement_task, self.annotator_a, {"label": "dog"})
        self.annotate(disagreement_task, self.annotator_c, {"label": "cat"})

        result = project_agreement(self.project)
        self.assertEqual(result["multi_annotated_task_count"], 2)
        self.assertEqual(result["agreement_task_count"], 2)
        self.assertEqual(result["pairwise_comparisons"], 2)
        self.assertEqual(result["exact_match_agreement"], 0.5)

    def test_tasks_without_two_distinct_annotators_are_not_compared(self):
        task = self.make_task("same-annotator")
        self.annotate(task, self.annotator_a, {"label": "cat"})
        self.annotate(task, self.annotator_a, {"label": "dog"})

        result = project_agreement(self.project)
        self.assertEqual(result["multi_annotated_task_count"], 0)
        self.assertEqual(result["pairwise_comparisons"], 0)
        self.assertIsNone(result["exact_match_agreement"])

    def test_empty_project_has_no_agreement_score(self):
        result = project_agreement(self.project)
        self.assertEqual(result["pairwise_comparisons"], 0)
        self.assertIsNone(result["exact_match_agreement"])

    def test_json_object_key_order_does_not_create_false_disagreement(self):
        task = self.make_task("key-order")
        self.annotate(task, self.annotator_a, {"label": "cat", "meta": {"x": 1, "y": 2}})
        self.annotate(task, self.annotator_b, {"meta": {"y": 2, "x": 1}, "label": "cat"})

        result = project_agreement(self.project)
        self.assertEqual(result["exact_match_agreement"], 1.0)
