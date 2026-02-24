from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import UserLoginForm

urlpatterns = [
    # Main Pages
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Auth System (Simple & Direct)
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html', 
        authentication_form=UserLoginForm 
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Health & Fitness Features
    path('profile/', views.profile, name='profile'),
    path('diet/', views.diet, name='diet'),
    path('workout/', views.workout, name='workout'),
    path('performance/', views.performance, name='performance'),
    
    # User Settings
    path('change-password/', views.change_password, name='change_password'),
]