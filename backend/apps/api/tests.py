from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.annotations.models import Annotation, AnnotationTask, Review
from apps.datasets.models import Dataset, Project


class HealthTest(APITestCase):
    def test_health(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class AuthenticationBoundaryTest(APITestCase):
    def test_project_api_requires_authentication(self):
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, 401)

    def test_metrics_api_requires_authentication(self):
        response = self.client.get("/api/projects/1/metrics/")
        self.assertEqual(response.status_code, 401)


class ProjectTest(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="demo", password="pass1234")
        self.other_user = user_model.objects.create_user(username="other", password="pass1234")
        self.client.force_authenticate(self.user)

    def test_create_project_assigns_authenticated_owner(self):
        response = self.client.post("/api/projects/", {"name": "Vision QA", "description": "Demo"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(Project.objects.get().owner, self.user)

    def test_cannot_create_dataset_inside_another_users_project(self):
        other_project = Project.objects.create(owner=self.other_user, name="Private")
        response = self.client.post("/api/datasets/", {"project": other_project.pk, "name": "Secret"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Dataset.objects.count(), 0)

    def test_project_list_does_not_disclose_other_users_projects(self):
        Project.objects.create(owner=self.user, name="Mine")
        Project.objects.create(owner=self.other_user, name="Theirs")
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data["results"]], ["Mine"])

    def _make_task(self):
        project = Project.objects.create(owner=self.user, name="Labelling")
        dataset = Dataset.objects.create(project=project, name="Images")
        return AnnotationTask.objects.create(
            dataset=dataset, external_id="img-001", payload={"image_url": "https://example.test/a.jpg"}
        )

    def test_task_cannot_be_submitted_without_annotations(self):
        task = self._make_task()
        response = self.client.post(f"/api/tasks/{task.pk}/submit/", {})
        self.assertEqual(response.status_code, 400)
        task.refresh_from_db()
        self.assertEqual(task.status, "pending")

    def test_claim_and_submit_requires_annotation(self):
        task = self._make_task()
        claim = self.client.post(f"/api/tasks/{task.pk}/claim/", {})
        self.assertEqual(claim.status_code, 200)
        annotation = self.client.post(
            "/api/annotations/",
            {"task": task.pk, "data": {"label": "cat"}, "confidence": 0.97}, format="json",
        )
        self.assertEqual(annotation.status_code, 201)
        submitted = self.client.post(f"/api/tasks/{task.pk}/submit/", {})
        self.assertEqual(submitted.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "submitted")

    def test_review_records_review_and_updates_task_state(self):
        task = self._make_task()
        task.assignee = self.user
        task.status = "in_progress"
        task.save()
        annotation = Annotation.objects.create(task=task, annotator=self.user, data={"label": "dog"})
        task.status = "submitted"
        task.save()
        response = self.client.post(
            f"/api/tasks/{task.pk}/review/", {"decision": "approved", "comment": "Looks good"}
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "approved")
        self.assertEqual(Review.objects.get(annotation=annotation).decision, "approved")

    def test_invalid_confidence_is_rejected(self):
        task = self._make_task()
        response = self.client.post(
            "/api/annotations/", {"task": task.pk, "data": {"label": "cat"}, "confidence": 3}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_metrics_only_return_owned_project(self):
        project = Project.objects.create(owner=self.user, name="Metrics")
        response = self.client.get(f"/api/projects/{project.pk}/metrics/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["task_count"], 0)
        self.assertIsNone(response.data["annotation_agreement"]["exact_match_agreement"])
        other_project = Project.objects.create(owner=self.other_user, name="Private")
        hidden = self.client.get(f"/api/projects/{other_project.pk}/metrics/")
        self.assertEqual(hidden.status_code, 404)
