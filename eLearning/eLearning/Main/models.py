from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Custom User model extending Django's AbstractUser. Adds role, real name, date of birth, bio, and profile photo fields.
class User(AbstractUser):

    ROLE_CHOICES = (
        ('ST', 'Student'),
        ('TE', 'Teacher'),
    )
    role = models.CharField(max_length=7, choices=ROLE_CHOICES, default='ST')
    real_name = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(verbose_name='Date of Birth', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='images/', blank=True, null=True, default='images/default.jpg')

    def clean(self):
        # Validate that non-superusers must have a role.
        if not self.is_superuser and not self.role:
            raise ValidationError('A user must have a role.')
        super().clean()

    def save(self, *args, **kwargs):
        # Validate model before saving.
        self.full_clean() 
        super().save(*args, **kwargs)

    def get_unread_notifications(self):
        # Helper method to get unread notifications for the user.
        return self.notifications.filter(read=False)

# Model to represent categories for courses
class Category(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        # String representation of the category.
        return self.name

# Represents a course with title, description, category, teacher, and timestamps.
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    students = models.ManyToManyField(User, through='Enrollment', related_name='courses_enrolled')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        # String representation of the course.
        return self.title

# Represents files associated with a course.   
class CourseFile(models.Model):
    course = models.ForeignKey(Course, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='course_files/')
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # String representation of the file.
        return f"{self.file.name} for {self.course.title}"

# Represents feedback left for a course.
class CourseFeedback(models.Model):
    course = models.ForeignKey(Course, related_name='feedback', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # String representation of the feedback.
        return f"Feedback by {self.user.get_full_name()} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

# Represents a student's enrollment in a course.
class Enrollment(models.Model):    
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # String representation of the post.
        return f"{self.student.username} enrolled in {self.course.title}"

# Represents a user's post or status update.
class UserPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_post')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # String representation of the post.
        return f"Status update by {self.user.get_full_name()} on {self.created_at}"

# Represents a notification sent to a user.
class Notification(models.Model):
    recipient = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)

    def __str__(self):
        # String representation of the notification.
        return f"Notification for {self.recipient.username}: {self.message}"