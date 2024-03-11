from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import *
from .forms import *
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

# Get the custom user model
User = get_user_model()


# User-Related Tests


# Testing the custom user model behavior and attributes
class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Creating users with different roles to test role behavior
        User.objects.create_user(username='student', email='student@example.com', role='ST')
        User.objects.create_user(username='teacher', email='teacher@example.com', role='TE')

    # Test user roles are correctly assigned
    def test_user_role(self):
        student = User.objects.get(username='student')
        teacher = User.objects.get(username='teacher')
        self.assertEqual(student.role, 'ST')
        self.assertEqual(teacher.role, 'TE')

    # Test validation for missing user role
    def test_user_clean(self):
        user = User(username='newuser', role='')  # Intentionally missing role
        with self.assertRaises(ValidationError):
            user.clean()

# Testing user form functionality, especially user creation and validation logic.
class UserFormTest(TestCase):
    def test_user_creation_form(self):
        # Validating the user creation form with all necessary fields filled in
        form_data = {
            'username': 'newuser',
            'password1': 'testpassword',
            'password2': 'testpassword',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'dob': '1990-01-01',
            'role': 'ST'
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid()) # Expect the form to be valid with the provided data

# Testing custom user model's save method to ensure custom validation and behavior are correctly implemented.
class CustomUserModelSaveTest(TestCase):
    def test_user_save(self):
        # Test the save method of a custom User model with custom validation logic
        user = User(username='save_test', email='save_test@example.com', role='ST')
        user.set_password('testpassword123')  # Setting the password correctly before saving
        try:
            user.save()
            self.assertTrue(True, "User saved successfully.") # Expect the save to succeed without ValidationError
        except ValidationError as e:
            self.fail(f"User.save() raised ValidationError unexpectedly! Errors: {e.message_dict}")

# Testing the user registration view to ensure that users can register successfully.
class UserRegistrationViewTest(TestCase):
    def setUp(self):
        # URL setup for the user registration page
        self.registration_url = reverse('register')

    def test_user_registration_view(self):
        # Test that a new user can register successfully and is redirected upon success
        response = self.client.post(self.registration_url, {
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'dob': '2000-01-01',
            'role': 'ST'
        })
        # Check for redirect to a new page, indicating success
        self.assertEqual(response.status_code, 302) # Expecting a redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists()) # New user should be created


# Course-Related Tests


# Testing model string representations and relationships
class CourseCategoryModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup for testing course and category relationship
        cls.teacher = User.objects.create_user(username='teacher', role='TE')
        cls.category = Category.objects.create(name='Science')
        cls.course = Course.objects.create(title='Biology 101', description='A course on Biology', teacher=cls.teacher, category=cls.category)

    # Test string representation of category
    def test_category_str(self):
        self.assertEqual(str(self.category), 'Science')

    # Test string representation of course
    def test_course_str(self):
        self.assertEqual(str(self.course), 'Biology 101')

# Testing the course editing functionality to ensure that courses can be edited successfully.
class CourseEditViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting up a course to be edited in the test
        cls.teacher = User.objects.create_user(username='edit_teacher', role='TE', password='123')
        cls.category = Category.objects.create(name='Literature')
        cls.course = Course.objects.create(title='Classic Literature', description='Exploring classics', teacher=cls.teacher, category=cls.category)

    def test_course_edit_view(self):
        # Test that the course edit view updates the course as expected
        self.client.login(username='edit_teacher', password='123')
        edit_url = reverse('course_edit', kwargs={'pk': self.course.pk})
        response = self.client.post(edit_url, {
            'title': 'Modern Literature',
            'description': 'Updated course description',  
            'category': self.course.category.id  
        })
        self.course.refresh_from_db()
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertEqual(self.course.title, 'Modern Literature') # Confirm title was updated
        self.assertEqual(self.course.description, 'Updated course description')  # Confirm description was updated

# Testing the cascade delete functionality to ensure related objects are also deleted when a course is deleted.
class CourseDeletionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting up a course with related objects like enrollments and feedback to test cascade deletion
        cls.teacher = User.objects.create_user(username='teacher_delete', role='TE')
        cls.student = User.objects.create_user(username='student_delete', role='ST')
        cls.category = Category.objects.create(name='Art')
        cls.course = Course.objects.create(title='Art History', description='A course on Art History', teacher=cls.teacher, category=cls.category)
        cls.enrollment = Enrollment.objects.create(student=cls.student, course=cls.course)
        cls.feedback = CourseFeedback.objects.create(course=cls.course, user=cls.student, content='Inspirational course.')
        cls.course_file = CourseFile.objects.create(course=cls.course, file='path/to/file', file_name='lecture.pdf')
        assert cls.course.pk is not None, "Failed to create and save the Course instance."

    def test_course_deletion_cascade(self):
        # Test that deleting a course also deletes related enrollments, feedback, and files
        course_to_delete = Course.objects.get(pk=self.course.pk)
        course_to_delete.delete()
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())
        self.assertFalse(Enrollment.objects.filter(id=self.enrollment.id).exists())
        self.assertFalse(CourseFeedback.objects.filter(id=self.feedback.id).exists())
        self.assertFalse(CourseFile.objects.filter(id=self.course_file.id).exists())

# Testing the permission check for course creation, ensuring students cannot create courses.
class CourseCreatePermissionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting up a student user who should not have permission to create a course
        cls.student = User.objects.create_user(username='student_no_create', role='ST', password='123')
        cls.category = Category.objects.create(name='Health')

    def test_student_cannot_create_course(self):
        # Test that a student user receives a 403 Forbidden response when attempting to create a course
        self.client.login(username='student_no_create', password='123')
        response = self.client.post(reverse('create_course'), {
            'title': 'Nutrition Basics',
            'description': 'Learn about nutrition',
            'category': self.category.id
        })
        # Check for 403 Forbidden response as the student should not have permission to create a course
        self.assertEqual(response.status_code, 403, "Student should receive a 403 Forbidden due to lack of permissions") # Expecting 403 Forbidden
        self.assertFalse(Course.objects.filter(title='Nutrition Basics').exists(), "Course should not be created by a student") # Course should not be created

# Testing the course form with invalid data to ensure form validation works as expected.
class CourseFormInvalidTest(TestCase):
    def test_invalid_form(self):
        # Test that the form is invalid when required fields are missing
        form_data = {'title': '', 'description': 'No title'}  # Missing title
        form = CourseForm(data=form_data)
        self.assertFalse(form.is_valid()) # Form should be invalid
        self.assertIn('title', form.errors) # Error should be raised for the missing title


# Enrollment and Feedback Tests
        

# Testing enrollment behavior
class EnrollmentModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup for testing enrollment relationships between users and courses
        teacher = User.objects.create_user(username='teacher_enrollment', role='TE')
        student = User.objects.create_user(username='student_enrollment', role='ST')
        category = Category.objects.create(name='Physics')
        course = Course.objects.create(title='Physics 101', description='A course on Physics', teacher=teacher, category=category)
        cls.enrollment = Enrollment.objects.create(student=student, course=course)

    # Test string representation of enrollment
    def test_enrollment_str(self):
        expected_str = f"{self.enrollment.student.username} enrolled in {self.enrollment.course.title}"
        self.assertEqual(str(self.enrollment), expected_str)

# Testing feedback submission and string representation within the course context.
class CourseFeedbackModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup for feedback functionality, requiring a course, teacher, and student
        teacher = User.objects.create_user(username='teacher_feedback', role='TE')
        student = User.objects.create_user(username='student_feedback', role='ST')
        category = Category.objects.create(name='Math')
        course = Course.objects.create(title='Calculus 101', description='A course on Calculus', teacher=teacher, category=category)
        cls.feedback = CourseFeedback.objects.create(course=course, user=student, content='Very helpful course.')

    def test_feedback_str(self):
        # Ensure feedback string representation includes user and timestamp for clarity
        expected_str = f"Feedback by {self.feedback.user.get_full_name()} on {self.feedback.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        self.assertEqual(str(self.feedback), expected_str)

# Testing the course enrollment and unenrollment functionalities from a user's perspective.
class CourseEnrollmentViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting up a test scenario with a teacher, student, and a course to enroll in
        cls.teacher = User.objects.create_user(username='teacher_course', role='TE', password='1234')
        cls.student = User.objects.create_user(username='student_course', role='ST', password='1234')
        cls.category = Category.objects.create(name='History')
        cls.course = Course.objects.create(title='History 101', description='A course on History', teacher=cls.teacher, category=cls.category)

    def test_enroll_course(self):
        # Test the process of a student enrolling in a course
        self.client.login(username='student_course', password='1234')
        response = self.client.get(reverse('enroll_course', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 302) # Expecting a redirect after successful enrollment
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists()) # Confirm enrollment

    def test_unenroll_student(self):
        # Test the process of a student being unenrolled from a course by a teacher
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='teacher_course', password='1234')
        response = self.client.get(reverse('unenroll_student', kwargs={'course_id': self.course.id, 'student_id': self.student.id}))
        self.assertEqual(response.status_code, 302) # Expecting a redirect after successful unenrollment
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists()) # Confirm unenrollment


# Notification and API Tests
        

# Testing the functionality to fetch unread notifications for a user.
class NotificationFetchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup for a user with unread notifications
        cls.user = User.objects.create_user(username='notified_user', role='ST', password='testpassword123')
        cls.unread_notification = Notification.objects.create(recipient=cls.user, message='Unread Message')
        cls.read_notification = Notification.objects.create(recipient=cls.user, message='Read Message', read=True)

    def test_fetch_unread_notifications(self):
        # Test that only unread notifications are fetched
        logged_in = self.client.login(username='notified_user', password='testpassword123')
        self.assertTrue(logged_in, "Failed to log in")
        fetch_url = reverse('fetch_notifications')
        response = self.client.get(fetch_url)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK but got {response.status_code}. Response: {response.content}")      # Expecting successful fetch   
        notifications = response.json()['notifications']
        self.assertEqual(len(notifications), 1) # Only one unread notification should be fetched
        self.assertEqual(notifications[0]['message'], 'Unread Message')  # Verify it's the correct notification
        self.assertFalse(notifications[0]['read']) # Verify the notification is indeed unread

# Testing the API interaction, specifically the creation of user posts through the API.
class UserPostAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting up a student user who will create a post via the API
        cls.user = User.objects.create_user(username='student', password='123', role='ST')

    def test_create_user_post(self):
        # Test creating a new user post through the API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('userpost-list'), {'content': 'Hello World'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # Expecting successful post creation
        self.assertEqual(UserPost.objects.count(), 1) # Confirming the post was added to the database
        self.assertEqual(UserPost.objects.get().content, 'Hello World') # Verifying the content of the created post


# Live Search Tests
        

# Testing the live search functionality
class LiveSearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.live_search_url = reverse('live_search')

        # Create a test user with a specific name for searching
        self.test_user = User.objects.create(
            username='testuser',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='ST'
        )

    # Test the live search response status
    def test_live_search(self):
        response = self.client.get(self.live_search_url, {'query': 'Test'})
        self.assertEqual(response.status_code, 200)


# Notification Model Tests
        

# Testing notifications behavior
class NotificationModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup for testing notifications linked to users and courses
        teacher = User.objects.create_user(username='teacher_notification', role='TE')
        student = User.objects.create_user(username='student_notification', role='ST')
        category = Category.objects.create(name='Chemistry')
        course = Course.objects.create(title='Chemistry 101', description='A course on Chemistry', teacher=teacher, category=category)
        cls.notification = Notification.objects.create(recipient=student, message='Welcome to Chemistry 101', course=course)

    # Test string representation of notification
    def test_notification_str(self):
        expected_str = f"Notification for {self.notification.recipient.username}: {self.notification.message}"
        self.assertEqual(str(self.notification), expected_str)


# Course and View Tests


# Further testing view functionalities, particularly focusing on course creation, editing, and permissions.
class CourseViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup necessary for creating and editing courses, including a teacher and a category
        cls.teacher = User.objects.create_user(username='teacher', role='TE', password='123')
        cls.category = Category.objects.create(name='Mathematics')

    def test_course_create_view(self):
        # Ensuring that courses can be created successfully and redirects occur as expected
        self.client.login(username='teacher', password='123')
        response = self.client.post(reverse('create_course'), {
            'title': 'Algebra 101',
            'description': 'Intro to Algebra',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, 302)  # Expect a redirect upon successful creation
        self.assertTrue(Course.objects.filter(title='Algebra 101').exists()) # Confirm course was created


# API Tests


# Testing API Viewsets, particularly useful for applications leveraging DRF for their API layer.
class CourseViewSetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setup includes a teacher and a course within a specific category, essential for API testing
        cls.teacher = User.objects.create_user(username='api_teacher', email='teacher@example.com', password='password123', role='TE')
        cls.category = Category.objects.create(name='Technology')
        cls.course = Course.objects.create(title='Python Programming', description='Learn Python', teacher=cls.teacher, category=cls.category)

    def setUp(self):
        self.client = APIClient() # Utilizing DRF's APIClient for authentication and request handling

    def test_retrieve_course(self):
        # Test course retrieval through the API, authenticating as the teacher
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse('course-detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200) # Successful retrieval gives a 200 OK response
        self.assertEqual(response.data['title'], 'Python Programming') # Data integrity check
        self.client.force_authenticate(user=None) 

# This test class is for testing the Course API functionality.
class CourseAPITest(TestCase):
    def test_course_list(self):
        client = APIClient()
        response = client.get('/api/courses/') # Make a GET request to the courses list API endpoint
        self.assertEqual(response.status_code, 200) # Assert the response status code is 200 (OK)


# Profile View Tests


# Testing profile viewing functionality to ensure user information is correctly displayed.
class ProfileViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Setting up a user whose profile will be viewed in the test
        cls.user = User.objects.create_user(username='user_profile', role='ST', password='1234')

    def test_profile_view(self):
        # Test viewing a user's profile
        self.client.login(username='user_profile', password='1234')
        response = self.client.get(reverse('profile', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200) # Expecting successful profile access
        self.assertContains(response, self.user.username) # Profile should contain the user's username


# AJAX Search Tests


# Testing the AJAX live search functionality to ensure it returns correct search results.
class AjaxSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Creating a user that should appear in search results
        cls.user = User.objects.create_user(
            username='searchable_user', 
            email='student@example.com', 
            password='testpassword', 
            role='ST',
            first_name='Searchable',  # Add first name
            last_name='User'  # Add last name
        )

    def test_live_search(self):
        # Test that the live search returns the correct user for the search query
        response = self.client.get(reverse('live_search'), {'query': 'Searchable'})
        self.assertIn('Searchable User', response.content.decode('utf-8'))


# Custom Form Tests
        

# This test class is designed to test the custom user creation form functionality.
class CustomUserCreationFormTest(TestCase):    
    def test_custom_user_creation_without_role(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'supersecurepassword',
            'password2': 'supersecurepassword',
            # 'role' is intentionally omitted
        }
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid()) # Check if form is invalid as expected
        self.assertIn('role', form.errors) # Check if 'role' is in form errors













