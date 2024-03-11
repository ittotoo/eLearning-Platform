from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import PasswordChangeView
from .models import *
from .forms import *
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse, JsonResponse
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .permissions import *
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Count, Q
from django.template.loader import render_to_string
import json

User = get_user_model()

# User-related Views

@login_required 
def user_post_update(request):
    # Allows users to update their status.
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:  # Make sure only students can post   
            UserPost.objects.create(user=request.user, content=content)
            messages.success(request, 'Status update posted.')
        else:
            messages.error(request, 'You cannot post an empty update.')
    return HttpResponseRedirect(reverse('profile'))

@login_required
def profile(request, username=None):
    # Displays the user profile.
    viewed_user = request.user if username is None else get_object_or_404(User, username=username)
    logged_in_user = request.user  # The currently authenticated user

    enrolled_courses = None
    if viewed_user.role == 'ST':
        enrolled_courses = viewed_user.courses_enrolled.all()

    courses = None
    if viewed_user.role == 'TE':
        courses = Course.objects.filter(teacher=viewed_user).annotate(student_count=Count('enrollment'))

    user_post = UserPost.objects.all().order_by('-created_at')

    return render(request, 'Main/profile.html', {
        'viewed_user': viewed_user, 
        'logged_in_user': logged_in_user,  # Always pass the logged_in_user for actions
        'courses': courses,
        'enrolled_courses': enrolled_courses,
        'user_post': user_post
    })

@login_required
def edit_profile(request):
    # Allows users to edit their profile.
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            if 'photo-clear' in request.POST:
                user.photo = 'images/default.jpg'
            user.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'Main/edit_profile.html', {'form': form, 'courses': courses})

#Views for the logout   
@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/login/')

# Views for the registration form  
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.photo = request.FILES.get('photo')
            print(f"Photo: {user.photo}")  # Debug print statement 
            user.save()
            print(f"User saved: {user}")  # Debug print statement 
            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'Main/register.html', {'form': form})


# Course-related Views


@login_required
def course_create(request):
    # Allows teachers to create a new course.
    if request.user.role != 'TE':
        return HttpResponseForbidden("You do not have permission to create courses.")

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            for i in range(len(request.FILES.getlist('files'))):
                file = request.FILES.getlist('files')[i]
                file_name = request.POST.get(f'file_name_{i}', file.name)  # Default to actual file name if custom name is absent
                CourseFile.objects.create(course=course, file=file, file_name=file_name)
            messages.success(request, 'Course created successfully.')
            return redirect('courses')
    else:
        form = CourseForm()
    return render(request, 'Main/course_create.html', {'form': form})

@login_required
def course_edit(request, pk):
    # Allows teachers to edit an existing course.
    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            new_files = []
            # Process each file and file name
            for index, f in enumerate(request.FILES.getlist('files')):
                # Construct the file name key based on the index
                file_name_key = f'file_name_{index}'
                file_name = request.POST.get(file_name_key, f.name)  # Default to actual file name if custom name is absent
                new_file = CourseFile.objects.create(course=course, file=f, file_name=file_name)
                new_files.append(new_file)

            if new_files:
                students_to_notify = course.students.all()
                for student in students_to_notify:
                    Notification.objects.create(
                        recipient=student,
                        message=f"New material added to {course.title}."
                    )

            messages.success(request, 'Course updated successfully.')
            return redirect('course_detail', pk=course.pk)
    else:
        form = CourseForm(instance=course)

    return render(request, 'Main/course_edit.html', {'form': form, 'course': course})

@login_required
def courses(request):
    # Displays a list of courses.
    categories = Category.objects.prefetch_related('course_set').all()
    if request.user.role == 'ST':
        enrolled_course_ids = list(request.user.courses_enrolled.values_list('id', flat=True))
    else:
        enrolled_course_ids = []
    return render(request, 'Main/courses.html', {'categories': categories, 'enrolled_course_ids': enrolled_course_ids})

@login_required
def course_detail(request, pk):
    # Displays details of a specific course.
    course = get_object_or_404(Course, pk=pk)
    is_teacher = request.user == course.teacher
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()

    if is_teacher or is_enrolled:
        feedback_form = CourseFeedbackForm()
        feedback_list = CourseFeedback.objects.filter(course=course).order_by('-created_at')

        if request.method == 'POST' and request.user.role == 'ST':
            feedback_form = CourseFeedbackForm(request.POST)
            if feedback_form.is_valid():
                feedback = feedback_form.save(commit=False)
                feedback.course = course
                feedback.user = request.user
                feedback.save()
                messages.success(request, 'Feedback submitted successfully.')
                return redirect('course_detail', pk=course.pk)

        context = {
            'course': course,
            'is_enrolled': is_enrolled,
            'feedback_form': feedback_form,
            'feedback_list': feedback_list,
        }

        return render(request, 'Main/course_detail.html', context)
    else:
        messages.error(request, "You do not have access to view this course.")
        return redirect('courses')

@login_required
def delete_course_file(request, file_id):
    # Allows teachers to delete course files.
    course_file = get_object_or_404(CourseFile, id=file_id)
    course = course_file.course
    if request.user != course.teacher:
        messages.error(request, "You are not allowed to delete this file.")
        return redirect('course_detail', pk=course.id)
    
    if request.method == "POST":
        course_file.file.delete()  # Optional: Deletes the file from the filesystem
        course_file.delete()
        messages.success(request, "File deleted successfully.")
        return redirect('course_detail', pk=course.id)
    else:
        messages.error(request, "This action is only allowed via POST.")
        return redirect('course_detail', pk=course.id)


# Enrollment-related Views


def enroll_course(request, course_id):
    # Enrolls the current user into a course.
    course = get_object_or_404(Course, pk=course_id)
    # Check if the enrollment is new to prevent duplicate notifications
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if created:
        # Create a notification for the teacher of the course
        Notification.objects.create(
            recipient=course.teacher,
            message=f"{request.user.get_full_name()} has enrolled in {course.title}."
        )
        messages.success(request, f"You have enrolled in the course: {course.title}")
    else:
        messages.info(request, f"You are already enrolled in the course: {course.title}")
    return redirect('course_detail', pk=course_id)

@login_required
def unenroll_student(request, course_id, student_id):
    # Allows teachers to unenroll students from a course.
    if request.user.role != 'TE':
        return HttpResponseForbidden("You are not allowed to unenroll students.")

    course = get_object_or_404(Course, id=course_id)
    # Ensure that the request user is the teacher of the course
    if request.user != course.teacher:
        return HttpResponseForbidden("You are not the teacher of this course.")
        
    student = get_object_or_404(User, id=student_id)

    # Perform the unenrollment
    Enrollment.objects.filter(course=course, student=student).delete()

    messages.success(request, f"{student.get_full_name()} has been unenrolled from {course.title}.")
    return redirect('course_students', course_id=course_id)

@login_required
def course_students(request, course_id):
    # Displays the students enrolled in a specific course for teachers.
    course = get_object_or_404(Course, pk=course_id)
    students = course.enrollment_set.all()

    # Check if the user is the teacher of the course
    if request.user != course.teacher:
        return HttpResponseForbidden("You are not allowed to view this page.")

    return render(request, 'Main/course_students.html', {
        'course': course,
        'students': students
    })


# Search and Miscellaneous Views


# Views for the search results   
def live_search(request):
    # Performs a live search of users.
    query = request.GET.get('query', '')
    if query:
        users = User.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query),
            Q(role='ST') | Q(role='TE')
        )
    else:
        users = User.objects.none()
    
    html = render_to_string('Main/live_results.html', {'users': users})
    return HttpResponse(html)

# Views for the Home Page 
def home(request):
    # Redirects to the profile page if authenticated, else to login.
    if request.user.is_authenticated:
        return redirect('profile')
    else:
        return redirect('login')

#Views for Chat Room
@login_required
def chat_room(request, course_id):
    # Manages the chat room for a course.
    course = get_object_or_404(Course, id=course_id)
    is_teacher = request.user == course.teacher
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()

    if not (is_teacher or is_enrolled):
        # Redirect if the user is neither the teacher nor enrolled
        return redirect('course_detail', pk=course_id)

    return render(request, 'Main/chat_room.html', {
        'course_id': course_id,
        'course': course,
        'user_id': request.user.id,
    })
   
@login_required
def read_notification(request, notification_id):
    # Marks a notification as read.
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.read = True
    notification.save()
    return redirect('profile')  # Adjust the redirection as needed

@login_required
def fetch_notifications(request):
    # Fetches unread notifications for the current user.
    notifications = request.user.notifications.filter(read=False).order_by('-created_at')[:5]  # Adjust the number as needed
    notifications_data = [{
        'id': notification.id,
        'message': notification.message,
        'read': notification.read
    } for notification in notifications]
    return JsonResponse({'notifications': notifications_data})


# API Views and ViewSets


class LatestUserPostsAPIView(APIView):
    # API view to get the latest posts.
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        latest_posts = UserPost.objects.select_related('user').all().order_by('-created_at')[:5]
        # Pass the request context to the serializer 
        serializer = UserPostSerializer(latest_posts, many=True, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, format=None):
        # Adjust this part as needed. Ensure you're not requiring unnecessary fields for POST.
        data = request.data.copy()
        data['user'] = request.user.pk
        serializer = UserPostSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserPostViewSet(viewsets.ModelViewSet):
    # ViewSet for user posts.
    queryset = UserPost.objects.all()
    serializer_class = UserPostSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserProfileViewSet(viewsets.ModelViewSet):
    # ViewSet for viewing and editing user profiles.
    serializer_class = UserProfileSerializer
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]  # Use appropriate permissions

    def get_queryset(self):
        queryset = super().get_queryset()
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(username=username)
        return queryset   
    
class UserViewSet(viewsets.ModelViewSet):
    # ViewSet for courses.
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsTeacher]

class CourseViewSet(viewsets.ModelViewSet):
    # ViewSet for courses.
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    def get_queryset(self):
        queryset = Course.objects.all()
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id is not None:
            queryset = queryset.filter(teacher__id=teacher_id)
        return queryset
    
class CourseFeedbackViewSet(viewsets.ModelViewSet):
    # ViewSet for course feedback.
    queryset = CourseFeedback.objects.all()
    serializer_class = CourseFeedbackSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CustomPasswordChangeView(PasswordChangeView):
    # Custom view for password change that adds success message.
    def form_valid(self, form):
        messages.success(self.request, 'Your password was successfully updated!')
        return super().form_valid(form)









   
