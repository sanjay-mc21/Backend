"""
URL configuration for adminportal project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from accounts.views import (
    LoginAPIView, 
    SuperAdminDashboardView, 
    AdminDashboardView, 
    ClientDashboardView,
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth endpoints
    path('api/login/', LoginAPIView.as_view(), name='login'),
    path('api/token-auth/', obtain_auth_token, name='token_auth'),
    
    # Dashboard endpoints
    path('api/dashboard/superadmin/', SuperAdminDashboardView.as_view(), name='superadmin_dashboard'),
    path('api/dashboard/admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('api/dashboard/client/', ClientDashboardView.as_view(), name='client_dashboard'),
    
    # Other API endpoints
    path('api/', include('accounts.urls')),
    path('api/', include('tasks.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

# Add media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 