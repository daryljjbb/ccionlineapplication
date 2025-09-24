from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Add this
    path('', include('webapp.urls')), # Keep this last
]

# This is the crucial part that serves media files during development.
# It checks if you are in DEBUG mode and then adds the URL pattern.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)