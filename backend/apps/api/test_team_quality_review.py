"""Tests for team management, configurable quality gates, and reviewer queues."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.annotations.models import Annotation, AnnotationSchema, AnnotationTask
from apps.datasets.models import Dataset, Project, ProjectMembership

class TeamQualityReviewApiTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="team-owner", password="pass1234")
        self.member = User.objects.create_user(username="team-member", password="pass1234")
        self.project = Project.objects.create(owner=self.owner, name="Team project")
        self.dataset = Dataset.objects.create(project=self.project, name="Review dataset")
        self.schema = AnnotationSchema.objects.create(dataset=self.dataset, name="Labels", label_type="classification", labels=["cat", "dog"])
        self.task = AnnotationTask.objects.create(dataset=self.dataset, external_id="review-queue-001", payload={"text": "cat"}, status="submitted")
        self.annotation = Annotation.objects.create(task=self.task, annotator=self.member, data={"label": "cat"}, confidence=0.4)
        self.client.force_authenticate(self.owner)

    def test_owner_can_add_list_and_remove_member(self):
        added = self.client.post(f"/api/projects/{self.project.pk}/members/", {"user_id": self.member.pk, "role": "reviewer"}, format="json")
        self.assertEqual(added.status_code, 201)
        self.assertEqual(added.data["role"], "reviewer")
        self.assertEqual(self.client.get(f"/api/projects/{self.project.pk}/members/").data[0]["username"], "team-member")
        self.assertEqual(self.client.delete(f"/api/projects/{self.project.pk}/members/{self.member.pk}/").status_code, 204)
        self.assertFalse(ProjectMembership.objects.filter(project=self.project, user=self.member).exists())

    def test_non_owner_cannot_manage_members(self):
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.post(f"/api/projects/{self.project.pk}/members/", {"user_id": self.owner.pk}, format="json").status_code, 404)

    def test_review_queue_lists_submitted_tasks_and_filters_dataset(self):
        AnnotationTask.objects.create(dataset=self.dataset, external_id="pending-queue-001", payload={}, status="pending")
        response = self.client.get(f"/api/tasks/review-queue/?dataset_id={self.dataset.pk}")
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual([item["external_id"] for item in results], ["review-queue-001"])
        self.assertEqual(self.client.get("/api/tasks/review-queue/?dataset_id=bad").status_code, 400)

    def test_configured_confidence_rule_is_applied_by_quality_check(self):
        created = self.client.post(f"/api/datasets/{self.dataset.pk}/quality-rules/",
            {"name": "Minimum confidence", "rule_type": "min_confidence", "parameters": {"minimum": 0.8}}, format="json")
        self.assertEqual(created.status_code, 201)
        checked = self.client.post(f"/api/tasks/{self.task.pk}/quality-check/", {"schema_id": self.schema.pk}, format="json")
        self.assertEqual(checked.status_code, 200)
        self.assertEqual(checked.data["invalid_count"], 1)
        self.assertIn("confidence_below_minimum", [issue["code"] for issue in checked.data["results"][0]["issues"]])

    def test_quality_rule_parameters_are_validated(self):
        response = self.client.post(f"/api/datasets/{self.dataset.pk}/quality-rules/",
            {"name": "Bad confidence", "rule_type": "min_confidence", "parameters": {"minimum": 1.5}}, format="json")
        self.assertEqual(response.status_code, 400)
