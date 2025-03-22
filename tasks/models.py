from django.db import models
from django.utils import timezone
from accounts.models import User, Location

class Task(models.Model):
    """Task model for managing client assignments"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    # Basic task information
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='tasks')
    
    # New fields for enhanced task form
    group_id = models.CharField(max_length=100, blank=True, null=True)
    site_name = models.CharField(max_length=200, blank=True, null=True)
    cluster = models.CharField(max_length=100, blank=True, null=True)
    service_engineer_name = models.CharField(max_length=200, blank=True, null=True)
    service_type = models.JSONField(default=list, blank=True, null=True)  # Store as a list of service types
    is_required = models.BooleanField(default=True)
    
    # Task assignment
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks',
                                  limit_choices_to={'role__in': [User.Role.ADMIN, User.Role.SUPERADMIN]})
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks',
                                  limit_choices_to={'role': User.Role.CLIENT})
    
    # Task dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField()
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Task status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    
    class Meta:
        ordering = ['-created_at']  # Order by most recent first
    
    def __str__(self):
        return self.title
    
    def is_overdue(self):
        if self.status not in [self.Status.COMPLETED, self.Status.APPROVED]:
            return timezone.now() > self.deadline
        return False

class TaskReport(models.Model):
    """Report submitted by client upon task completion"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='reports')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_reports',
                                   limit_choices_to={'role': User.Role.CLIENT})
    report_text = models.TextField()
    attachments = models.FileField(upload_to='task_reports/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Review information
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='reviewed_reports',
                                   limit_choices_to={'role__in': [User.Role.ADMIN, User.Role.SUPERADMIN]})
    reviewed_at = models.DateTimeField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-submitted_at']  # Order by most recent first
    
    def __str__(self):
        return f"Report for {self.task.title}"
