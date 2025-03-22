from rest_framework import serializers
from .models import Task, TaskReport
from accounts.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'location', 'location_name',
                  'assigned_by', 'assigned_by_name', 'assigned_to', 'assigned_to_name',
                  'created_at', 'updated_at', 'deadline', 'completed_at',
                  'status', 'is_overdue', 'group_id', 'site_name', 'cluster',
                  'service_engineer_name', 'service_type', 'is_required']

class TaskReportSerializer(serializers.ModelSerializer):
    """Serializer for TaskReport model"""
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TaskReport
        fields = ['id', 'task', 'task_title', 'submitted_by', 'submitted_by_name',
                  'report_text', 'attachments', 'submitted_at',
                  'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'feedback']

class TaskDetailSerializer(TaskSerializer):
    """Detailed Task serializer with reports included"""
    reports = TaskReportSerializer(many=True, read_only=True)
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['reports'] 