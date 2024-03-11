from django.contrib import admin
from .models import *

# Enhance UserAdmin with additional options
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')

# Category admin configuration
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

# Course admin configuration with detailed view
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'teacher', 'created_at', 'updated_at')

# Enrollment admin to manage course enrollments
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')

# Notification admin for better management
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'course', 'read')
    list_filter = ('read', 'course')

# UserPost admin for user-generated content
class UserPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    search_fields = ('user__username', 'content')

# CourseFeedback admin for feedback management
class CourseFeedbackAdmin(admin.ModelAdmin):
    list_display = ('course', 'user', 'content', 'created_at')
    list_filter = ('course',)

# CourseFile admin to manage course files
class CourseFileAdmin(admin.ModelAdmin):
    list_display = ('course', 'file_name', 'uploaded_at')
    search_fields = ('course__title', 'file_name')

# Register models and their admin classes
admin.site.register(User, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(UserPost, UserPostAdmin)
admin.site.register(CourseFeedback, CourseFeedbackAdmin)
admin.site.register(CourseFile, CourseFileAdmin)