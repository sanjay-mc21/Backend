from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Custom User model with role-based authentication"""
    
    class Role(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', _('SuperAdmin')
        ADMIN = 'ADMIN', _('Admin')
        CLIENT = 'CLIENT', _('Client')
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT,
    )
    
    # Additional fields
    location = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_client(self):
        return self.role == self.Role.CLIENT

class Location(models.Model):
    """Model for managing locations/states"""
    class StateName(models.TextChoices):
        TAMIL_NADU = 'TAMIL_NADU', _('Tamil Nadu')
        ANDHRA_PRADESH = 'ANDHRA_PRADESH', _('Andhra Pradesh')
        TELANGANA = 'TELANGANA', _('Telangana')
        ODISHA = 'ODISHA', _('Odisha')
    
    name = models.CharField(
        max_length=20,
        choices=StateName.choices,
        unique=True,
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.get_name_display()
        
class AdminLocation(models.Model):
    """Model for mapping admins to their managed locations"""
    admin = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': User.Role.ADMIN},
        related_name='assigned_location'
    )
    location = models.ForeignKey(
        Location, 
        on_delete=models.CASCADE,
        related_name='assigned_admins'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admin.username} - {self.location.get_name_display()}"
