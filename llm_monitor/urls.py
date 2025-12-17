"""
URL configuration for llm_monitor project.

Main URL router that includes all application URLs.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('accounts/', include('allauth.urls')),
    
    # Dashboard App URLs (both API and frontend views)
    path('', include('dashboard.urls')),
    
    # API endpoints under /api/ prefix
    path('api/', include('dashboard.api_urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
