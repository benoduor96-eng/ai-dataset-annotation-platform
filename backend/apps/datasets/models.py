from django.conf import settings
from django.db import models

class Project(models.Model):
    name=models.CharField(max_length=160)
    description=models.TextField(blank=True)
    owner=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='projects')
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class Dataset(models.Model):
    project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name='datasets')
    name=models.CharField(max_length=160)
    description=models.TextField(blank=True)
    item_count=models.PositiveIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
