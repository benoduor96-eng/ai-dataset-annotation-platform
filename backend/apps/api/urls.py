from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, DatasetViewSet, SchemaViewSet, TaskViewSet, AnnotationViewSet, ReviewViewSet, project_export
router=DefaultRouter()
router.register('projects',ProjectViewSet,basename='projects'); router.register('datasets',DatasetViewSet,basename='datasets'); router.register('schemas',SchemaViewSet,basename='schemas'); router.register('tasks',TaskViewSet,basename='tasks'); router.register('annotations',AnnotationViewSet,basename='annotations'); router.register('reviews',ReviewViewSet,basename='reviews')
urlpatterns=[path('',include(router.urls)),path('projects/<int:pk>/export/',project_export)]
