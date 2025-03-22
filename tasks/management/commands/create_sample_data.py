"""
Management command to create sample data for testing.
Run using: python manage.py create_sample_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from accounts.models import User, Location

class Command(BaseCommand):
    help = 'Creates sample users, locations, and tasks for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        # Create client user if needed
        try:
            client_user = User.objects.filter(role='CLIENT').first()
            if not client_user:
                client_user = User.objects.create_user(
                    username='client',
                    email='client@example.com',
                    password='client123',
                    role='CLIENT',
                    is_staff=False,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"Created client user: {client_user.username}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Using existing client user: {client_user.username}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting/creating client user: {e}"))
            return

        # Create admin user if needed
        try:
            admin_user = User.objects.filter(role__in=['ADMIN', 'SUPERADMIN']).first()
            if not admin_user:
                admin_user = User.objects.create_user(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    role='ADMIN',
                    is_staff=True,
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"Created admin user: {admin_user.username}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Using existing admin user: {admin_user.username}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting/creating admin user: {e}"))
            return

        # Create location if needed
        try:
            location = Location.objects.first()
            if not location:
                location = Location.objects.create(
                    name='TAMIL_NADU',
                    description='Tamil Nadu State'
                )
                self.stdout.write(self.style.SUCCESS(f"Created location: {location}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Using existing location: {location}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting/creating location: {e}"))
            return

        # Create sample tasks
        try:
            task_count = Task.objects.count()
            self.stdout.write(self.style.SUCCESS(f"Current task count: {task_count}"))
            
            if task_count == 0:
                # Task 1 - Pending
                Task.objects.create(
                    title="Sample Task 1",
                    description="This is a sample pending task for testing purposes",
                    location=location,
                    assigned_by=admin_user,
                    assigned_to=client_user,
                    deadline=timezone.now() + timedelta(days=7),
                    status=Task.Status.PENDING
                )

                # Task 2 - In Progress
                Task.objects.create(
                    title="Sample Task 2",
                    description="This is a sample in-progress task for testing purposes",
                    location=location,
                    assigned_by=admin_user,
                    assigned_to=client_user,
                    deadline=timezone.now() + timedelta(days=5),
                    status=Task.Status.IN_PROGRESS
                )

                # Task 3 - Completed
                Task.objects.create(
                    title="Sample Task 3",
                    description="This is a sample completed task for testing purposes",
                    location=location,
                    assigned_by=admin_user,
                    assigned_to=client_user,
                    deadline=timezone.now() + timedelta(days=3),
                    status=Task.Status.COMPLETED,
                    completed_at=timezone.now()
                )

                self.stdout.write(self.style.SUCCESS("Created 3 sample tasks"))
            else:
                self.stdout.write(self.style.SUCCESS("Tasks already exist, skipping creation"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating sample tasks: {e}")) 