from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.datasets.models import Project
class HealthTest(APITestCase):
    def test_health(self):
        r=self.client.get('/api/health/'); self.assertEqual(r.status_code,200); self.assertEqual(r.data['status'],'ok')
class ProjectTest(APITestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username='demo',password='pass1234')
        self.client.force_authenticate(self.user)
    def test_create_project(self):
        r=self.client.post('/api/projects/',{'name':'Vision QA','description':'Demo'}); self.assertEqual(r.status_code,201); self.assertEqual(Project.objects.count(),1)
