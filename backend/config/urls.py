from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.api.views import health
urlpatterns=[path('admin/',admin.site.urls),path('api/health/',health),path('api/auth/token/',TokenObtainPairView.as_view()),path('api/auth/token/refresh/',TokenRefreshView.as_view()),path('api/',include('apps.api.urls'))]
