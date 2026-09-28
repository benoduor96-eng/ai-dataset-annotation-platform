import os
from pathlib import Path
from datetime import timedelta
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-secret')
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','corsheaders','rest_framework','apps.users','apps.datasets','apps.annotations']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware']
ROOT_URLCONF='config.urls'
TEMPLATES=[{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION='config.wsgi.application'
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.getenv('POSTGRES_DB','annotation'),'USER':os.getenv('POSTGRES_USER','annotation'),'PASSWORD':os.getenv('POSTGRES_PASSWORD','annotation'),'HOST':os.getenv('POSTGRES_HOST','localhost'),'PORT':os.getenv('POSTGRES_PORT','5432')}}
AUTH_PASSWORD_VALIDATORS=[]
LANGUAGE_CODE='en-us'; TIME_ZONE='UTC'; USE_I18N=True; USE_TZ=True
STATIC_URL='static/'; DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
CORS_ALLOWED_ORIGINS=[x for x in os.getenv('CORS_ALLOWED_ORIGINS','http://localhost:5173').split(',') if x]
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':('rest_framework_simplejwt.authentication.JWTAuthentication',),'DEFAULT_PERMISSION_CLASSES':('rest_framework.permissions.IsAuthenticated',)}
SIMPLE_JWT={'ACCESS_TOKEN_LIFETIME':timedelta(minutes=60),'REFRESH_TOKEN_LIFETIME':timedelta(days=7)}
CELERY_BROKER_URL=os.getenv('REDIS_URL','redis://localhost:6379/0')
CELERY_RESULT_BACKEND=CELERY_BROKER_URL
