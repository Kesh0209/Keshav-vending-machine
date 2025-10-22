from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),  # keep admin path here
    path('', include('machine_app.urls')),  # this loads your vending machine interface
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
