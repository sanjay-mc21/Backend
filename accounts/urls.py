from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LocationViewSet, AdminLocationViewSet, TestPostView, CreateAdminView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'admin-locations', AdminLocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('test-post/', TestPostView.as_view(), name='test-post'),
    path('create-admin/', CreateAdminView.as_view(), name='create-admin'),
] 