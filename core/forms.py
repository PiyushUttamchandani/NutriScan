from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

# -------- REGISTER FORM --------
class RegisterForm(forms.ModelForm):
    # Styling password fields to match your theme
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Create Password',
        'class': 'w-full px-5 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl outline-none focus:border-[#0fa36b]'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password',
        'class': 'w-full px-5 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl outline-none focus:border-[#0fa36b]'
    }), label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Choose Username',
                'class': 'w-full px-5 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl outline-none focus:border-[#0fa36b]'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter Email',
                'class': 'w-full px-5 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl outline-none focus:border-[#0fa36b]'
            }),
        }

    # 1. Username Validation
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another one.")
        return username

    # 2. Email Validation
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    # 3. Password Match & Complexity
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)
            
        return cleaned_data


# -------- USER PROFILE FORM --------
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'height_feet', 'height_inches', 'weight', 'gender', 'goal']
        # Aap chahein toh yahan bhi widgets add karke styling improve kar sakte hain

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age < 10 or age > 100:
            raise ValidationError("Please enter a valid age between 10 and 100.")
        return age

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight <= 0:
            raise ValidationError("Weight must be a positive number.")
        return weight

    def clean_height_feet(self):
        feet = self.cleaned_data.get('height_feet')
        if feet < 1 or feet > 8:
            raise ValidationError("Height (feet) must be between 1 and 8.")
        return feet


# -------- LOGIN FORM --------
class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Username',
        'class': 'w-full px-5 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl outline-none focus:border-[#0fa36b]'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Password',
        'class': 'w-full px-5 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl outline-none focus:border-[#0fa36b]'
    }))

    def clean(self):
        try:
            return super().clean()
        except ValidationError:
            raise ValidationError("Invalid username or password. Please try again.")