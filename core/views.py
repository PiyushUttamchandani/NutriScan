from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from collections import defaultdict
from datetime import date, timedelta

from .models import UserProfile, DietPlan, WorkoutPlan, WorkoutLog
from .forms import UserProfileForm, RegisterForm

# ---------------- HOME ----------------
def home(request):
    return render(request, 'home.html')

# ---------------- REGISTER (Updated with Verification) 
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user) # Register hote hi login kar do
            return redirect('profile') # Profile setup par bhejo
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# ---------------- ACTIVATE ACCOUNT ----------------
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True # User ko active kar do
        user.save()
        return render(request, 'registration/activation_success.html')
    else:
        return render(request, 'registration/activation_invalid.html')

# ---------------- PROFILE (ONBOARDING + VIEW) ----------------
@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if not profile.is_profile_complete:
        if request.method == 'POST':
            form = UserProfileForm(request.POST, instance=profile)
            if form.is_valid():
                onboarding_profile = form.save(commit=False)
                onboarding_profile.is_profile_complete = True
                onboarding_profile.save()
                return redirect('dashboard')
        else:
            form = UserProfileForm(instance=profile)
        return render(request, 'onboarding.html', {'form': form})

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'profile.html', {'profile': profile, 'form': form})

# ---------------- DASHBOARD (Safe Check) ----------------
@login_required
def dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.is_profile_complete:
            return redirect('profile')
    except UserProfile.DoesNotExist:
        return redirect('profile')

    # BMI CALCULATIONS
    total_inches = (profile.height_feet * 12) + profile.height_inches
    height_m = total_inches * 0.0254
    bmi = profile.weight / (height_m ** 2) if height_m > 0 else 0
    
    if bmi < 18.5: category = "Underweight"
    elif bmi < 25: category = "Normal"
    elif bmi < 30: category = "Overweight"
    else: category = "Obese"

    # CALORIES
    calories = 1800 if profile.goal == 'loss' else 2500 if profile.goal == 'gain' else 2200

    return render(request, 'dashboard.html', {
        'profile': profile, 'bmi': round(bmi, 2), 'category': category, 'calories': calories
    })

# ---------------- DIET ----------------
@login_required
def diet(request):
    profile = UserProfile.objects.get(user=request.user)
    plan = DietPlan.objects.filter(goal=profile.goal).first()
    return render(request, 'diet.html', {'plan': plan, 'profile': profile})

# ---------------- WORKOUT ----------------
@login_required
def workout(request):
    profile = UserProfile.objects.get(user=request.user)
    plan = WorkoutPlan.objects.filter(goal=profile.goal).first()

    if request.method == 'POST':
        selected = request.POST.getlist('exercise')
        for ex in selected:
            WorkoutLog.objects.create(user=request.user, exercise=ex, completed=True)
        return redirect('performance')

    return render(request, 'workout.html', {'plan': plan, 'profile': profile})

# ---------------- PERFORMANCE ----------------
@login_required
def performance(request):
    logs = WorkoutLog.objects.filter(user=request.user).order_by('-date')
    grouped_logs = defaultdict(list)
    for log in logs:
        grouped_logs[log.date].append(log.exercise)

    daily_score = {d: len(exercises) for d, exercises in grouped_logs.items()}
    workout_days = sorted(set(log.date for log in logs), reverse=True)
    streak = 0
    today = date.today()
    for day in workout_days:
        if day == today - timedelta(days=streak): streak += 1
        else: break

    week_ago = today - timedelta(days=7)
    weekly_logs = WorkoutLog.objects.filter(user=request.user, date__gte=week_ago)
    workout_days_count = len(set(log.date for log in weekly_logs))
    total_exercises = weekly_logs.count()
    avg_per_day = round(total_exercises / workout_days_count, 2) if workout_days_count > 0 else 0

    sorted_data = sorted(daily_score.items())
    labels = [d.strftime("%d %b") for d, v in sorted_data]
    values = [v for d, v in sorted_data]

    profile = UserProfile.objects.filter(user=request.user).first()
    form = UserProfileForm(instance=profile)

    return render(request, 'performance.html', {
        'grouped_logs': dict(grouped_logs), 'daily_score': daily_score, 'streak': streak,
        'labels': labels, 'values': values, 'workout_days_count': workout_days_count,
        'total_exercises': total_exercises, 'avg_per_day': avg_per_day, 'profile': profile, 'form': form
    })