from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *
from django.utils.dateformat import DateFormat
from django.utils.formats import get_format

User = get_user_model()

# Serializer for the User model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role', 'email', 'first_name', 'last_name', 'dob']

    # Custom create method to handle user creation with role validation
    def create(self, validated_data):
        user = super().create(validated_data)
        if self.context['request'].user.role != 'TE':
            raise serializers.ValidationError("You do not have permission to create a user.")
        return user

    # Custom update method to restrict user updates to teachers
    def update(self, instance, validated_data):
        if self.context['request'].user.role != 'TE':
            raise serializers.ValidationError("You do not have permission to update a user.")
        return super().update(instance, validated_data)
    
# Serializer for the Course model with nested category and teacher
class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'teacher', 'students', 'category']

# Serializer for CourseFeedback model with user details
class CourseFeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.get_full_name')

    class Meta:
        model = CourseFeedback
        fields = '__all__'

# Serializer for UserPost with dynamic user information
class UserPostSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    user_photo_url = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = UserPost
        # Including the user in write_only to avoid exposing user details in response 
        fields = ['id', 'user', 'content', 'created_at', 'user_full_name', 'user_photo_url', 'user_role']
        extra_kwargs = {'user': {'write_only': True, 'required': False}}

    # Method to get the URL of the user's photo
    def get_user_photo_url(self, obj):
        request = self.context.get('request')
        if obj.user.photo and hasattr(obj.user.photo, 'url'):
            photo_url = obj.user.photo.url
            return request.build_absolute_uri(photo_url)
        return None
    
    # Method to get the role of the user who made the post
    def get_user_role(self, obj):
        role = obj.user.get_role_display()
        #print(f"Fetching role for user {obj.user.username}: {role}")
        return role
    
    # Method to get the full name of the user who made the post
    def get_user_full_name(self, obj):
        return obj.user.get_full_name()
    
    def get_created_at(self, obj):
        # Format `created_at` using Django's default date-time format
        return DateFormat(obj.created_at).format(get_format('DATETIME_FORMAT'))

# Serializer for UserProfile
class UserProfileSerializer(serializers.ModelSerializer):
    # Ensuring comprehensive user profile data is provided
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'real_name', 'dob', 'bio', 'photo']
