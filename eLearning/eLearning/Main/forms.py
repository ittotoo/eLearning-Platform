from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import DateInput
from .models import *

# Custom form for creating new users, extending Django's UserCreationForm.
class CustomUserCreationForm(UserCreationForm):
    # Additional fields to capture more information during user registration.
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    dob = forms.DateField(required=True, label='Date of Birth', widget=DateInput(attrs={'type': 'date'}))
    bio = forms.CharField(required=False, widget=forms.Textarea)
    photo = forms.ImageField(required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)


    class Meta(UserCreationForm.Meta):
        model = get_user_model()  # Specifies to use the custom user model.  
        fields = ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'dob', 'bio', 'photo', 'role')

    def clean(self):
        # Custom validation to ensure a role is selected.
        cleaned_data = super().clean()
        role = cleaned_data.get("role")

        if not role:
            raise ValidationError("You must select a role.")
        return cleaned_data

# Custom form for changing user information, extending Django's UserChangeForm.    
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'dob', 'bio', 'photo',)

    def clean(self):
        cleaned_data = super().clean()
        remove_photo = cleaned_data.get('remove_photo')
        if remove_photo:
            cleaned_data['photo'] = 'images/default.jpg'
        return cleaned_data

# Form for creating and updating Course objects.    
class CourseForm(forms.ModelForm):
    # Custom widgets to enhance the form's appearance.
    title = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Title'})
    )
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Course Description', 'rows': '3'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Course # Specifies to use the Course model.
        fields = ['title', 'description', 'category']

# Form for submitting feedback on a Course.
class CourseFeedbackForm(forms.ModelForm):
    class Meta:
        model = CourseFeedback # Specifies to use the CourseFeedback model.
        fields = ['content'] # Only includes the 'content' field for feedback text.