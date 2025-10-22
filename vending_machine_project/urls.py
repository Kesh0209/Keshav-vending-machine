from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

# Auto-create superuser if it doesn't exist
from django.contrib.auth.models import User
import os

if not User.objects.filter(username='keshav').exists() and os.environ.get('RENDER'):
    User.objects.create_superuser('keshav', 'keshavasukhai@gmail.com', 'Keshkaranlol02')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('machine_app.urls')),
]

# Serve media files in ALL environments (development and production)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
