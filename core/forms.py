from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile


# -------- REGISTER FORM --------
class RegisterForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username','email']

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        validate_password(password)

        return cleaned_data


# -------- USER PROFILE FORM --------
class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = [
            'age',
            'height_feet',
            'height_inches',
            'weight',
            'gender',
            'goal'
        ]