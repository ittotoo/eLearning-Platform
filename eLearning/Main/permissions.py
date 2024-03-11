from rest_framework import permissions

# Custom permission class to check if the current user is a teacher.
class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        # Returns True if the user's role is 'TE' for teacher or if the user is a superuser, granting access.
        return request.user.role == 'TE' or request.user.is_superuser

# Custom permission class to check if the current user is a student.  
class IsStudent(permissions.BasePermission):
    # Custom permission to only allow students to access certain actions.

    def has_permission(self, request, view):
        # Check if the user is authenticated and has a role of 'ST' (Student)
        return request.user and request.user.is_authenticated and request.user.role == 'ST'