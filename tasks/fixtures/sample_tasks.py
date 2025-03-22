"""
Script to add sample tasks to the database.
Run this using: python manage.py shell < tasks/fixtures/sample_tasks.py
"""

from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from accounts.models import User, Location

def create_sample_tasks():
    print("Creating sample tasks...")
    
    # Make sure we have at least one client user
    try:
        client_user = User.objects.filter(role='CLIENT').first()
        if not client_user:
            client_user = User.objects.create(
                username='client',
                email='client@example.com',
                role='CLIENT',
                is_staff=False,
                is_active=True
            )
            client_user.set_password('client123')
            client_user.save()
            print(f"Created client user: {client_user.username}")
    except Exception as e:
        print(f"Error getting or creating client user: {e}")
        return

    # Make sure we have at least one admin or superadmin user
    try:
        admin_user = User.objects.filter(role__in=['ADMIN', 'SUPERADMIN']).first()
        if not admin_user:
            admin_user = User.objects.create(
                username='admin',
                email='admin@example.com',
                role='ADMIN',
                is_staff=True,
                is_active=True
            )
            admin_user.set_password('admin123')
            admin_user.save()
            print(f"Created admin user: {admin_user.username}")
    except Exception as e:
        print(f"Error getting or creating admin user: {e}")
        return

    # Make sure we have at least one location
    try:
        location = Location.objects.first()
        if not location:
            location = Location.objects.create(
                name='TAMIL_NADU',
                description='Tamil Nadu State'
            )
            print(f"Created location: {location}")
    except Exception as e:
        print(f"Error getting or creating location: {e}")
        return

    # Create sample tasks
    try:
        # Only create tasks if there are none
        if Task.objects.count() == 0:
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

            print(f"Created 3 sample tasks")
        else:
            print(f"Tasks already exist, skipping creation")
    except Exception as e:
        print(f"Error creating sample tasks: {e}")

if __name__ == "__main__":
    create_sample_tasks()

# Call the function to create sample tasks
create_sample_tasks() 