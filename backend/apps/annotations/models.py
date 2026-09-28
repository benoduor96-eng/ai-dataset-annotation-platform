from django.conf import settings
from django.db import models
from apps.datasets.models import Dataset

class AnnotationSchema(models.Model):
    LABEL_TYPES=[('classification','Classification'),('ner','Named Entity'),('bbox','Bounding Box'),('segmentation','Segmentation')]
    dataset=models.ForeignKey(Dataset,on_delete=models.CASCADE,related_name='schemas')
    name=models.CharField(max_length=160)
    label_type=models.CharField(max_length=32,choices=LABEL_TYPES)
    labels=models.JSONField(default=list)
    version=models.PositiveIntegerField(default=1)

class AnnotationTask(models.Model):
    STATUS=[('pending','Pending'),('in_progress','In Progress'),('submitted','Submitted'),('approved','Approved'),('rejected','Rejected')]
    dataset=models.ForeignKey(Dataset,on_delete=models.CASCADE,related_name='tasks')
    external_id=models.CharField(max_length=160,unique=True)
    payload=models.JSONField(default=dict)
    assignee=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name='assigned_tasks')
    status=models.CharField(max_length=20,choices=STATUS,default='pending')
    ai_suggestions=models.JSONField(default=list)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class Annotation(models.Model):
    task=models.ForeignKey(AnnotationTask,on_delete=models.CASCADE,related_name='annotations')
    annotator=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    data=models.JSONField(default=dict)
    confidence=models.FloatField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

class Review(models.Model):
    annotation=models.OneToOneField(Annotation,on_delete=models.CASCADE,related_name='review')
    reviewer=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    decision=models.CharField(max_length=20,choices=[('approved','Approved'),('rejected','Rejected')])
    comment=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
