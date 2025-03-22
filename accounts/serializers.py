from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Location, AdminLocation

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 
                  'role', 'location', 'phone_number', 'profile_picture']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)

class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    class Meta:
        model = Location
        fields = ['id', 'name', 'description', 'created_at']

class AdminLocationSerializer(serializers.ModelSerializer):
    """Serializer for AdminLocation model"""
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = AdminLocation
        fields = ['id', 'admin', 'admin_username', 'location', 'location_name', 'assigned_date'] 