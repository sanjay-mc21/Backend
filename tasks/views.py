from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from .models import Task, TaskReport
from .serializers import TaskSerializer, TaskReportSerializer, TaskDetailSerializer
from accounts.views import IsAdminOrSuperAdmin

class TaskViewSet(viewsets.ModelViewSet):
    """API viewset for managing tasks"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_serializer_class(self):
        """Return detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
    
    def get_permissions(self):
        """
        SuperAdmin can perform any action.
        Admin can create, update, and view tasks.
        Client can only view assigned tasks and update their status.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrSuperAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role and assigned location"""
        user = self.request.user
        if user.is_superadmin():
            return Task.objects.all()
        elif user.is_admin():
            # Admin can only see tasks within their assigned location
            try:
                admin_location = user.assigned_location
                return Task.objects.filter(location=admin_location.location)
            except:
                # If admin has no assigned location, show nothing
                return Task.objects.none()
        else:
            # Client can only see tasks assigned to them
            return Task.objects.filter(assigned_to=user)
    
    def perform_create(self, serializer):
        """Set assigned_by to current user and validate location"""
        user = self.request.user
        if user.is_admin():
            # Make sure admin creates tasks only for their location
            try:
                admin_location = user.assigned_location
                location = serializer.validated_data.get('location')
                if location != admin_location.location:
                    raise serializers.ValidationError("You can only create tasks for your assigned location.")
            except:
                raise serializers.ValidationError("You don't have an assigned location.")
                
        serializer.save(assigned_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        """Mark a task as in progress"""
        task = self.get_object()
        if task.assigned_to != request.user and not request.user.is_admin() and not request.user.is_superadmin():
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        task.status = Task.Status.IN_PROGRESS
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark a task as completed"""
        task = self.get_object()
        if task.assigned_to != request.user:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        task.status = Task.Status.COMPLETED
        task.completed_at = timezone.now()
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve_task(self, request, pk=None):
        """Approve a completed task"""
        task = self.get_object()
        if not request.user.is_admin() and not request.user.is_superadmin():
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        if task.status != Task.Status.COMPLETED:
            return Response({"detail": "Task is not completed yet."}, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = Task.Status.APPROVED
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject_task(self, request, pk=None):
        """Reject a completed task"""
        task = self.get_object()
        if not request.user.is_admin() and not request.user.is_superadmin():
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        if task.status != Task.Status.COMPLETED:
            return Response({"detail": "Task is not completed yet."}, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = Task.Status.REJECTED
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

class TaskReportViewSet(viewsets.ModelViewSet):
    """API viewset for managing task reports"""
    queryset = TaskReport.objects.all()
    serializer_class = TaskReportSerializer
    
    def get_permissions(self):
        """
        SuperAdmin and Admin can view all reports.
        Client can create reports and view their own reports.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminOrSuperAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role and assigned location"""
        user = self.request.user
        if user.is_superadmin():
            return TaskReport.objects.all()
        elif user.is_admin():
            # Admin can only see reports for tasks within their assigned location
            try:
                admin_location = user.assigned_location
                return TaskReport.objects.filter(task__location=admin_location.location)
            except:
                # If admin has no assigned location, show nothing
                return TaskReport.objects.none()
        else:
            # Client can only see reports they submitted
            return TaskReport.objects.filter(submitted_by=user)
    
    def perform_create(self, serializer):
        """Set submitted_by to current user"""
        serializer.save(submitted_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def review_report(self, request, pk=None):
        """Review a task report"""
        report = self.get_object()
        if not request.user.is_admin() and not request.user.is_superadmin():
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        
        feedback = request.data.get('feedback', '')
        approved = request.data.get('approved', False)
        
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.feedback = feedback
        report.save()
        
        # Update task status based on approval
        task = report.task
        if approved:
            task.status = Task.Status.APPROVED
        else:
            task.status = Task.Status.REJECTED
        task.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)
