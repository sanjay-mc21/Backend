from django.shortcuts import render
from rest_framework import viewsets, permissions, status, views, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Count, Q
from rest_framework.authtoken.models import Token
from .models import Location, AdminLocation, User
from .serializers import UserSerializer, LocationSerializer, AdminLocationSerializer
from tasks.models import Task, TaskReport

User = get_user_model()

class IsSuperAdmin(permissions.BasePermission):
    """Permission for SuperAdmin access"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superadmin()

class IsAdminOrSuperAdmin(permissions.BasePermission):
    """Permission for Admin or SuperAdmin access"""
    def has_permission(self, request, view):
        return request.user and (request.user.is_admin() or request.user.is_superadmin())

class UserViewSet(viewsets.ModelViewSet):
    """API viewset for managing users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    parser_classes = [
        parsers.JSONParser,
        parsers.FormParser,
        parsers.MultiPartParser,
    ]
    
    def get_permissions(self):
        """
        SuperAdmin can perform any action.
        Admin can only view users (for assigning tasks).
        Users can only view and update their own profile.
        """
        if self.action in ['create', 'destroy']:
            permission_classes = [IsSuperAdmin]
        elif self.action in ['list']:
            permission_classes = [IsAdminOrSuperAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user role and assigned location"""
        user = self.request.user
        if user.is_superadmin():
            return User.objects.all()
        elif user.is_admin():
            try:
                # Admins can only see clients in their assigned location
                admin_location = user.assigned_location
                return User.objects.filter(
                    role=User.Role.CLIENT,
                    location=admin_location.location.get_name_display()
                )
            except:
                # If admin has no assigned location, show no clients
                return User.objects.none()
        else:
            # Clients can only see their own profile
            return User.objects.filter(id=user.id)
    
    def update(self, request, *args, **kwargs):
        """Check permissions for update"""
        user = self.get_object()
        if not request.user.is_superadmin() and request.user.id != user.id:
            return Response({"detail": "Not authorized to edit this user."}, 
                           status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Create a new user and handle location assignment for admins"""
        # Debug request information
        print(f"Content-Type: {request.content_type}")
        print(f"Request data: {request.data}")
        print(f"Request body: {request.body}")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Create the user
            user = serializer.save()
            
            # If this is an admin user and location_code is provided, assign the location
            if user.role == User.Role.ADMIN and 'location_code' in request.data:
                location_code = request.data.get('location_code')
                if location_code:
                    try:
                        # Get the location object
                        location = Location.objects.get(name=location_code)
                        
                        # Create AdminLocation connection
                        AdminLocation.objects.create(
                            admin=user,
                            location=location
                        )
                        
                        # Also set the display name in the user's location field
                        user.location = location.get_name_display()
                        user.save()
                    except Location.DoesNotExist:
                        # Location not found, continue without error
                        pass
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def clients(self, request):
        """Return only client users for task assignment, filtered by admin's location"""
        if not (request.user.is_admin() or request.user.is_superadmin()):
            return Response({"detail": "Not authorized."}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        if request.user.is_superadmin():
            clients = User.objects.filter(role=User.Role.CLIENT)
        else:
            try:
                # Filter clients by admin's location
                admin_location = request.user.assigned_location
                clients = User.objects.filter(
                    role=User.Role.CLIENT, 
                    location=admin_location.location.get_name_display()
                )
            except:
                clients = User.objects.none()
                
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Return the current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class LocationViewSet(viewsets.ModelViewSet):
    """API viewset for managing locations"""
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    
    def get_permissions(self):
        """
        SuperAdmin can perform any action.
        Admin can only view locations.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsSuperAdmin]
        else:
            permission_classes = [IsAdminOrSuperAdmin]
        return [permission() for permission in permission_classes]

class AdminLocationViewSet(viewsets.ModelViewSet):
    """API viewset for managing admin-location mappings"""
    queryset = AdminLocation.objects.all()
    serializer_class = AdminLocationSerializer
    permission_classes = [IsSuperAdmin]

class LoginAPIView(views.APIView):
    """
    API endpoint for user login
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'detail': 'Please provide both username and password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # For demo purposes, allow any password for demo users
        if username in ['superadmin', 'tnadmin', 'apadmin', 'tsadmin', 'odadmin',
                        'tnclient1', 'tnclient2', 'tnclient3', 
                        'apclient1', 'apclient2', 'apclient3',
                        'tsclient1', 'tsclient2', 'tsclient3',
                        'odclient1', 'odclient2', 'odclient3']:
            # Get or create user
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create user with role based on username
                role = 'CLIENT'
                if username == 'superadmin':
                    role = 'SUPERADMIN'
                elif 'admin' in username:
                    role = 'ADMIN'
                
                # Determine location based on username prefix
                location = ''
                if 'tn' in username:
                    location = 'Tamil Nadu'
                elif 'ap' in username:
                    location = 'Andhra Pradesh'
                elif 'ts' in username:
                    location = 'Telangana'
                elif 'od' in username:
                    location = 'Odisha'
                
                user = User.objects.create_user(
                    username=username,
                    password='demopassword',  # Set a default password
                    email=f'{username}@example.com',
                    role=role,
                    location=location
                )
            
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'location': user.location
                }
            })
        
        # For non-demo users, authenticate normally
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({
                'detail': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'location': user.location
            }
        })

class SuperAdminDashboardView(views.APIView):
    """
    API endpoint for SuperAdmin dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Only SuperAdmin role can access this data
        if user.role != 'SUPERADMIN':
            return Response({
                'detail': 'You do not have permission to access this data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get counts
        total_admins = User.objects.filter(role='ADMIN').count()
        total_clients = User.objects.filter(role='CLIENT').count()
        active_tasks = Task.objects.filter(status__in=['PENDING', 'IN_PROGRESS']).count()  # Use uppercase to match enum values
        completed_tasks = Task.objects.filter(status__in=['COMPLETED', 'APPROVED']).count()  # Use uppercase to match enum values
        
        # Get location statistics
        locations = ['Tamil Nadu', 'Andhra Pradesh', 'Telangana', 'Odisha']
        location_stats = []
        
        from django.db.models import Count
        
        # Process each location
        for location_name in locations:
            # Find location code from the name
            for choice in Location.StateName.choices:
                if choice[1] == location_name:
                    location_code = choice[0]
                    try:
                        # Get location object
                        location_obj = Location.objects.get(name=location_code)
                        
                        # Get admin and client counts for this location
                        location_admins = AdminLocation.objects.filter(location=location_obj).count()
                        location_clients = User.objects.filter(
                            role='CLIENT',
                            location=location_name
                        ).count()
                        
                        # Get task counts and completion rate
                        location_tasks = Task.objects.filter(location=location_obj).count()
                        completed_location_tasks = Task.objects.filter(
                            location=location_obj,
                            status__in=['COMPLETED', 'APPROVED']
                        ).count()
                        
                        # Calculate completion rate (defaults to 0 if no tasks)
                        completion_rate = 0
                        if location_tasks > 0:
                            completion_rate = completed_location_tasks / location_tasks
                        
                        location_stats.append({
                            'name': location_code,  # Code name used for API calls
                            'display_name': location_name,  # Human-readable name for display
                            'code': location_code,  # For backward compatibility
                            'admin_count': location_admins,
                            'client_count': location_clients,
                            'task_count': location_tasks,
                            'performance': completion_rate
                        })
                    except Location.DoesNotExist:
                        # Handle the case where the location doesn't exist
                        continue
        
        # Get admin users for the admin management page
        admin_users = []
        for admin in User.objects.filter(role='ADMIN'):
            try:
                # Try to get the assigned location
                admin_location = AdminLocation.objects.get(admin=admin)
                location_name = admin_location.location.get_name_display()
            except AdminLocation.DoesNotExist:
                location_name = 'Not assigned'
            
            admin_users.append({
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'location': location_name
            })
        
        # Get recent activity
        recent_tasks = Task.objects.all().order_by('-updated_at')[:5]
        recent_reports = TaskReport.objects.all().order_by('-submitted_at')[:5]
        
        # Combine and sort activities
        recent_activity = []
        
        for task in recent_tasks:
            if task.status == 'COMPLETED':  # Use uppercase to match enum values
                action = 'Task completed'
            elif task.status == 'APPROVED':
                action = 'Task approved'
            elif task.status == 'IN_PROGRESS':
                action = 'Task started'
            else:
                action = 'Task assigned'
                
            recent_activity.append({
                'action': action,
                'details': f'Task #{task.id} in {task.location}',
                'time': task.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        for report in recent_reports:
            recent_activity.append({
                'action': 'Report submitted',
                'details': f'Report for Task #{report.task.id}',
                'time': report.submitted_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Sort all activities by time (most recent first)
        recent_activity.sort(key=lambda x: x['time'], reverse=True)
        
        # Format activities for display
        formatted_activities = []
        for activity in recent_activity[:5]:  # Limit to 5 most recent
            formatted_activities.append({
                'description': activity['action'],
                'user_name': activity['details'],
                'time_ago': activity['time']
            })
        
        # Return all data
        return Response({
            'total_admins': total_admins,
            'total_clients': total_clients,
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
            'locations': location_stats,
            'admin_users': admin_users,
            'recent_activities': formatted_activities
        })

class AdminDashboardView(views.APIView):
    """
    API endpoint for Admin dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Only Admin role can access this data
        if user.role != 'ADMIN':
            return Response({
                'detail': 'You do not have permission to access this data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get counts for admin's location
        location_name = user.location
        
        # Convert location name to location code
        location_code = None
        if location_name == 'Tamil Nadu':
            location_code = 'TAMIL_NADU'
        elif location_name == 'Andhra Pradesh':
            location_code = 'ANDHRA_PRADESH'
        elif location_name == 'Telangana':
            location_code = 'TELANGANA'
        elif location_name == 'Odisha':
            location_code = 'ODISHA'
        
        # Find the location object instead of using the string
        try:
            location_obj = Location.objects.get(name=location_code) if location_code else None
            
            # Use the location object in the filters
            total_clients = User.objects.filter(role='CLIENT', location=location_name).count()
            
            # Filter using the location object rather than the string name
            active_tasks = Task.objects.filter(
                status__in=['PENDING', 'IN_PROGRESS'],  # Use uppercase to match enum values
                location=location_obj
            ).count() if location_obj else 0
            
            pending_reports = TaskReport.objects.filter(
                task__location=location_obj,
                reviewed_at__isnull=True
            ).count() if location_obj else 0
        except Location.DoesNotExist:
            # Handle the case where location doesn't exist
            total_clients = 0
            active_tasks = 0
            pending_reports = 0
        
        # Task completion rates - we'll create mock data for this demo
        task_completion = {
            'this_week': 0.85 if location_name == 'Tamil Nadu' else 
                         0.82 if location_name == 'Andhra Pradesh' else
                         0.78 if location_name == 'Telangana' else 0.75,
            'this_month': 0.75 if location_name == 'Tamil Nadu' else 
                          0.72 if location_name == 'Andhra Pradesh' else
                          0.68 if location_name == 'Telangana' else 0.65,
            'this_quarter': 0.65 if location_name == 'Tamil Nadu' else 
                            0.62 if location_name == 'Andhra Pradesh' else
                            0.58 if location_name == 'Telangana' else 0.55,
            'this_year': 0.80 if location_name == 'Tamil Nadu' else 
                         0.77 if location_name == 'Andhra Pradesh' else
                         0.73 if location_name == 'Telangana' else 0.70,
        }
        
        # Get recent activity - ensure we use the location object for filtering
        recent_tasks = Task.objects.filter(location=location_obj).order_by('-updated_at')[:5] if location_obj else []
        recent_reports = TaskReport.objects.filter(
            task__location=location_obj
        ).order_by('-submitted_at')[:5] if location_obj else []
        
        # Combine and sort activities
        recent_activity = []
        
        for task in recent_tasks:
            if task.status == 'COMPLETED':  # Use uppercase to match enum values
                action = 'Task completed'
            elif task.status == 'APPROVED':
                action = 'Task approved'
            elif task.status == 'IN_PROGRESS':
                action = 'Task started'
            else:
                action = 'Task assigned'
                
            recent_activity.append({
                'action': action,
                'details': f'Task #{task.id}',
                'client': task.assigned_to.username,
                'time': task.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        for report in recent_reports:
            action = 'Report submitted'
            if report.reviewed_at:
                action = 'Report reviewed'
                
            recent_activity.append({
                'action': action,
                'details': f'For Task #{report.task.id}',
                'client': report.task.assigned_to.username,
                'time': report.submitted_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Sort by time
        recent_activity = sorted(
            recent_activity, 
            key=lambda x: x['time'], 
            reverse=True
        )[:5]
        
        return Response({
            'total_clients': total_clients,
            'active_tasks': active_tasks,
            'pending_reports': pending_reports,
            'task_completion': task_completion,
            'recent_activity': recent_activity
        })

class ClientDashboardView(views.APIView):
    """
    API endpoint for Client dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Only Client role can access this data
        if user.role != 'CLIENT':
            return Response({
                'detail': 'You do not have permission to access this data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get task counts for this client
        assigned_tasks = Task.objects.filter(assigned_to=user).count()
        completed_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=['COMPLETED', 'APPROVED']  # Use uppercase to match enum values
        ).count()
        pending_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=['PENDING', 'IN_PROGRESS']  # Use uppercase to match enum values
        ).count()
        
        # Get upcoming deadlines
        import datetime
        today = datetime.date.today()
        
        # For demo, create some upcoming deadlines
        upcoming_tasks = Task.objects.filter(
            assigned_to=user,
            status__in=['PENDING', 'IN_PROGRESS']  # Use uppercase to match enum values
        ).order_by('deadline')[:3]
        
        upcoming_deadlines = []
        for task in upcoming_tasks:
            # Calculate days left (for demo, use random days)
            import random
            days_left = random.randint(1, 5)
            
            upcoming_deadlines.append({
                'task_id': task.id,
                'days_left': days_left,
                'is_urgent': days_left <= 2
            })
        
        # Get recent activity
        recent_tasks = Task.objects.filter(assigned_to=user).order_by('-updated_at')[:3]
        recent_reports = TaskReport.objects.filter(
            submitted_by=user
        ).order_by('-submitted_at')[:3]
        
        # Combine and sort activities
        recent_activity = []
        
        for task in recent_tasks:
            if task.status == 'COMPLETED':  # Use uppercase to match enum values
                action = 'Task completed'
            elif task.status == 'APPROVED':
                action = 'Task approved'
            elif task.status == 'IN_PROGRESS':
                action = 'Task started'
            else:
                action = 'Task assigned'
                
            recent_activity.append({
                'action': action,
                'details': f'Task #{task.id}',
                'time': task.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        for report in recent_reports:
            action = 'Report submitted'
            if report.reviewed_at:
                action = 'Report reviewed'
                
            recent_activity.append({
                'action': action,
                'details': f'For Task #{report.task.id}',
                'time': report.submitted_at.strftime('%Y-%m-%d %H:%M')
            })
        
        # Sort by time
        recent_activity = sorted(
            recent_activity, 
            key=lambda x: x['time'], 
            reverse=True
        )[:5]
        
        return Response({
            'assigned_tasks': assigned_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'upcoming_deadlines': upcoming_deadlines,
            'recent_activity': recent_activity
        })

class TestPostView(views.APIView):
    """
    Test view for debugging POST requests
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]
    
    def post(self, request, format=None):
        """Echo back the request data for debugging"""
        print(f"Test POST received")
        print(f"Content-Type: {request.content_type}")
        print(f"Request data type: {type(request.data)}")
        print(f"Request data: {request.data}")
        print(f"Request body: {request.body}")
        
        return Response({
            'received_data': request.data,
            'content_type': request.content_type,
            'method': request.method
        })

class CreateAdminView(views.APIView):
    """
    Dedicated view for creating admin users
    """
    permission_classes = [IsSuperAdmin]
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]
    
    def post(self, request, format=None):
        """Create a new admin user"""
        print("CreateAdminView - POST received")
        print(f"Content-Type: {request.content_type}")
        print(f"Request data: {request.data}")
        
        # Extract data from request
        data = request.data.copy()
        data['role'] = 'ADMIN'
        
        # Create the user with serializer
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            # Create the user
            user = serializer.save()
            
            # If location_code is provided, assign the location
            if 'location_code' in data:
                location_code = data.get('location_code')
                if location_code:
                    print(f"Trying to find location with code: {location_code}")
                    
                    # Debug available locations
                    all_locations = Location.objects.all()
                    print(f"Available locations: {[(loc.name, loc.get_name_display()) for loc in all_locations]}")
                    
                    # First try direct name lookup
                    try:
                        location = Location.objects.get(name=location_code)
                        print(f"Found location by code: {location.name}")
                    except Location.DoesNotExist:
                        # Try to match with display name instead
                        location = None
                        for loc in all_locations:
                            if loc.get_name_display() == location_code:
                                location = loc
                                print(f"Found location by display name: {location.name}")
                                break
                    
                    if location:
                        # Create AdminLocation connection
                        AdminLocation.objects.create(
                            admin=user,
                            location=location
                        )
                        
                        # Also set the display name in the user's location field
                        user.location = location.get_name_display()
                        user.save()
                        print(f"Successfully assigned location {location.get_name_display()} to user {user.username}")
                    else:
                        print(f"Could not find location with code or name: {location_code}")
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        print(f"Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
