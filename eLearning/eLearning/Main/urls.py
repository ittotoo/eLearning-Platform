from django.urls import path, reverse_lazy, include
from . import views
from django.contrib.auth import views as auth_views
from .views import *
from rest_framework.routers import DefaultRouter
from django.views.decorators.csrf import csrf_exempt

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'feedback', views.CourseFeedbackViewSet)
router.register(r'userposts', views.UserPostViewSet)
router.register(r'profiles', views.UserProfileViewSet)

urlpatterns = [
    path('', views.home, name='home'), # Home page route.
    path('api/', include(router.urls)), # API root endpoint including registered routers.
    path('register/', views.register, name='register'), # User registration route.
    path('logout/', views.user_logout, name='logout'), # User logout route.
    path('login/', auth_views.LoginView.as_view(template_name='Main/login.html'), name='login'), # User login route, uses Django's built-in auth views.
    path('change_password/', CustomPasswordChangeView.as_view(template_name='Main/change_password.html', success_url=reverse_lazy('home')), name='change_password'), # Password change route.
    path('profile/', views.profile, name='profile'), # Profile view route, can also view other users' profiles.
    path('profile/<str:username>/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'), # Edit user profile route.
    path('create_course/', views.course_create, name='create_course'), # Course creation route.
    path('courses/', views.courses, name='courses'), # View all courses route.
    path('edit_course/<int:pk>/', course_edit, name='course_edit'), # Course edit route.
    path('course_detail/<int:pk>/', course_detail, name='course_detail'), # Detailed course view route.
    path('delete_course_file/<int:file_id>/', views.delete_course_file, name='delete_course_file'), # Delete a course file route.
    path('enroll_course/<int:course_id>/', views.enroll_course, name='enroll_course'), # Enroll in a course route.
    path('course_students/<int:course_id>/', views.course_students, name='course_students'), # View all students enrolled in a course.
    path('user_post_update/', views.user_post_update, name='user_post_update'), # Update user post route (e.g., for status updates).
    path('live-search/', views.live_search, name='live_search'), # AJAX live search route.     
    path('api/latest_user_posts/', LatestUserPostsAPIView.as_view(), name='latest_user_posts'), # Fetch the latest user posts via API.
    path('chat/<int:course_id>/', chat_room, name='chat_room'), # Chat room for a specific course.
    path('course/<int:course_id>/unenroll/<int:student_id>/', csrf_exempt(views.unenroll_student), name='unenroll_student'), # Unenroll a student from a course.
    path('notifications/read/<int:notification_id>/', views.read_notification, name='read_notification'), # Mark a notification as read.
    path('fetch_notifications/', views.fetch_notifications, name='fetch_notifications'), # Fetch unread notifications.
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), # Include default login and logout views for the browsable API.
]
