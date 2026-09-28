from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from rest_framework import viewsets, decorators, response
from apps.datasets.models import Project, Dataset
from apps.annotations.models import AnnotationSchema, AnnotationTask, Annotation, Review
from .serializers import ProjectSerializer, DatasetSerializer, SchemaSerializer, TaskSerializer, AnnotationSerializer, ReviewSerializer

def health(request): return JsonResponse({'status':'ok','service':'django-platform'})

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class=ProjectSerializer
    def get_queryset(self): return Project.objects.filter(owner=self.request.user).annotate(task_count=Count('datasets__tasks'))
    def perform_create(self,serializer): serializer.save(owner=self.request.user)

class DatasetViewSet(viewsets.ModelViewSet):
    serializer_class=DatasetSerializer
    def get_queryset(self): return Dataset.objects.filter(project__owner=self.request.user)

class SchemaViewSet(viewsets.ModelViewSet):
    serializer_class=SchemaSerializer
    def get_queryset(self): return AnnotationSchema.objects.filter(dataset__project__owner=self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class=TaskSerializer
    def get_queryset(self): return AnnotationTask.objects.filter(dataset__project__owner=self.request.user)
    @decorators.action(detail=True,methods=['post'])
    def submit(self,request,pk=None):
        task=self.get_object(); task.status='submitted'; task.save(update_fields=['status','updated_at']); return response.Response(self.get_serializer(task).data)
    @decorators.action(detail=True,methods=['post'])
    def review(self,request,pk=None):
        task=self.get_object(); decision=request.data.get('decision')
        if decision not in ('approved','rejected'): return response.Response({'detail':'decision must be approved or rejected'},status=400)
        task.status=decision; task.save(update_fields=['status','updated_at']); return response.Response(self.get_serializer(task).data)

class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class=AnnotationSerializer
    def get_queryset(self): return Annotation.objects.filter(task__dataset__project__owner=self.request.user)
    def perform_create(self,serializer): serializer.save(annotator=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class=ReviewSerializer
    def get_queryset(self): return Review.objects.filter(annotation__task__dataset__project__owner=self.request.user)
    def perform_create(self,serializer): serializer.save(reviewer=self.request.user)

@decorators.api_view(['get'])
def project_export(request,pk):
    project=Project.objects.filter(pk=pk,owner=request.user).first()
    if not project: return response.Response({'detail':'Not found'},status=404)
    rows=[]
    for task in AnnotationTask.objects.filter(dataset__project=project).prefetch_related('annotations'):
        for ann in task.annotations.all(): rows.append({'task_id':task.external_id,'payload':task.payload,'annotation':ann.data,'confidence':ann.confidence})
    import json
    return HttpResponse(json.dumps(rows,indent=2),content_type='application/json',headers={'Content-Disposition':f'attachment; filename="project-{pk}.json"'})
