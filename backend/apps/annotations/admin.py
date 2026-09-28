from django.contrib import admin
from .models import AnnotationSchema, AnnotationTask, Annotation, Review
admin.site.register([AnnotationSchema,AnnotationTask,Annotation,Review])
