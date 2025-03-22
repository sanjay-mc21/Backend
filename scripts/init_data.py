#!/usr/bin/env python
import os
import sys
import django

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adminbackend.settings')
django.setup()

from accounts.models import User, Location, AdminLocation
from django.utils import timezone
from datetime import timedelta

def init_data():
    print("Initializing database with demo data...")
    
    # Create locations (states)
    print("Creating locations...")
    states = {
        Location.StateName.TAMIL_NADU: "Tamil Nadu state in southern India",
        Location.StateName.ANDHRA_PRADESH: "Andhra Pradesh state in southern India",
        Location.StateName.TELANGANA: "Telangana state in southern India",
        Location.StateName.ODISHA: "Odisha state in eastern India",
    }
    
    locations = {}
    for state_code, description in states.items():
        location, created = Location.objects.get_or_create(
            name=state_code,
            defaults={'description': description}
        )
        locations[state_code] = location
        if created:
            print(f"  Created location: {location.get_name_display()}")
        else:
            print(f"  Location exists: {location.get_name_display()}")
    
    # Create users
    print("\nCreating users...")
    
    # SuperAdmin user
    superadmin, created = User.objects.get_or_create(
        username='superadmin',
        defaults={
            'email': 'superadmin@example.com',
            'first_name': 'Super',
            'last_name': 'Admin',
            'role': User.Role.SUPERADMIN,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        superadmin.set_password('superadmin')
        superadmin.save()
        print("  Created SuperAdmin user: superadmin")
    else:
        print("  SuperAdmin user exists: superadmin")
    
    # Admin users for each state
    state_admins = {
        Location.StateName.TAMIL_NADU: ('tnadmin', 'Tamil Nadu Admin'),
        Location.StateName.ANDHRA_PRADESH: ('apadmin', 'Andhra Pradesh Admin'),
        Location.StateName.TELANGANA: ('tsadmin', 'Telangana Admin'),
        Location.StateName.ODISHA: ('odadmin', 'Odisha Admin'),
    }
    
    for state_code, (username, full_name) in state_admins.items():
        first_name, last_name = full_name.split(' ', 1)
        admin, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': first_name,
                'last_name': last_name,
                'role': User.Role.ADMIN,
                'location': locations[state_code].get_name_display(),
                'is_staff': True,
            }
        )
        
        if created:
            admin.set_password(username)
            admin.save()
            print(f"  Created Admin user: {username}")
        else:
            print(f"  Admin user exists: {username}")
        
        # Assign admin to location
        admin_location, created = AdminLocation.objects.get_or_create(
            admin=admin,
            defaults={'location': locations[state_code]}
        )
        
        if created:
            print(f"  Assigned {username} to {locations[state_code].get_name_display()}")
        else:
            if admin_location.location != locations[state_code]:
                admin_location.location = locations[state_code]
                admin_location.save()
                print(f"  Updated {username}'s location to {locations[state_code].get_name_display()}")
            else:
                print(f"  {username} already assigned to {locations[state_code].get_name_display()}")
    
    # Create client users for each state
    print("\nCreating client users...")
    for state_code, location in locations.items():
        state_name = location.get_name_display()
        state_code_short = state_code.split('_')[0].lower()
        
        # Create 3 clients for each state
        for i in range(1, 4):
            username = f"{state_code_short}client{i}"
            client, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'{state_name}',
                    'last_name': f'Client {i}',
                    'role': User.Role.CLIENT,
                    'location': state_name,
                }
            )
            
            if created:
                client.set_password(username)
                client.save()
                print(f"  Created Client user: {username} in {state_name}")
            else:
                print(f"  Client user exists: {username}")
    
    print("\nInitialization completed successfully!")

if __name__ == "__main__":
    init_data() 