from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import UserLoginForm

urlpatterns = [

    # ---------------- MAIN PAGES ----------------
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # ---------------- AUTH ----------------
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        authentication_form=UserLoginForm
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),

    # ---------------- USER ----------------
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),

    # ---------------- FITNESS FEATURES ----------------
    path('diet/', views.diet, name='diet'),
    path('workout/', views.workout, name='workout'),
    path('performance/', views.performance, name='performance'),

    # ---------------- FOOD PHOTO ANALYZER ----------------
    path('food-scan/', views.food_scan, name='food_scan'),
    path('api/analyze-food/', views.analyze_food_api, name='analyze_food_api'),
    path('api/log-food-scan/', views.log_food_scan, name='log_food_scan'),

]