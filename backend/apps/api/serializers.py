from rest_framework import serializers
from apps.datasets.models import Project, Dataset
from apps.annotations.models import AnnotationSchema, AnnotationTask, Annotation, Review
class ProjectSerializer(serializers.ModelSerializer):
    class Meta: model=Project; fields='__all__'
class DatasetSerializer(serializers.ModelSerializer):
    class Meta: model=Dataset; fields='__all__'
class SchemaSerializer(serializers.ModelSerializer):
    class Meta: model=AnnotationSchema; fields='__all__'
class TaskSerializer(serializers.ModelSerializer):
    class Meta: model=AnnotationTask; fields='__all__'
class AnnotationSerializer(serializers.ModelSerializer):
    class Meta: model=Annotation; fields='__all__'
class ReviewSerializer(serializers.ModelSerializer):
    class Meta: model=Review; fields='__all__'
