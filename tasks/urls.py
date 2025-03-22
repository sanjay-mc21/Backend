from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TaskReportViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'task-reports', TaskReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 