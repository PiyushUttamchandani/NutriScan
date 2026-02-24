from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from datetime import date, timedelta

from .models import UserProfile, DietPlan, WorkoutPlan, WorkoutLog
from .forms import UserProfileForm, RegisterForm

# ---------------- HOME ----------------
def home(request):
    return render(request, 'home.html')


# ---------------- REGISTER (Simple & CSRF Exempt) ----------------
@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_active = True 
            user.save()
            login(request, user)
            return redirect('profile')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


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


# ---------------- DASHBOARD (Main Logic) ----------------
from django.db.models import Sum
@login_required
def dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.is_profile_complete:
            return redirect('profile')
    except UserProfile.DoesNotExist:
        return redirect('profile')

    # 1. BMI Calculation
    total_inches = (profile.height_feet * 12) + profile.height_inches
    height_m = total_inches * 0.0254
    bmi = round(profile.weight / (height_m ** 2), 2) if height_m > 0 else 0
    
    if bmi < 18.5: 
        category = "Underweight"
    elif bmi < 25: 
        category = "Normal"
    elif bmi < 30: 
        category = "Overweight"
    else: 
        category = "Obese"

    # 2. Base Goal Calories
    if profile.goal == 'loss':
        base_target = 1800
    elif profile.goal == 'gain':
        base_target = 2500
    else: # Maintain
        base_target = 2200

    # 3. Dynamic Calculation Logic
    # Summing up all burned calories for today
    today_stats = WorkoutLog.objects.filter(
        user=request.user, 
        date=date.today()
    ).aggregate(total=Sum('calories_burned'))
    
    total_burned = today_stats['total'] or 0

    # 4. Handle Negative Values for UI
    # We use max(0, ...) so that it never shows -200 on your dashboard
    remaining_calories = base_target - total_burned
    if remaining_calories < 0:
        remaining_calories = 0

    return render(request, 'dashboard.html', {
        'profile': profile, 
        'bmi': bmi, 
        'category': category, 
        'calories': remaining_calories, 
        'base_target': base_target,
        'total_burned': total_burned
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
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect('profile')

    plan = WorkoutPlan.objects.filter(goal=profile.goal).first()

    # Calculate 1/3rd of the base target for the logic: 3 Workouts = Goal Met
    if profile.goal == 'loss':
        base_target = 1800
    elif profile.goal == 'gain':
        base_target = 2500
    else:
        base_target = 2200
    
    # Each workout deducts 33.3% of the daily goal
    calories_per_workout = base_target // 3

    if request.method == 'POST':
        selected_exercises = request.POST.getlist('exercise')
        
        for ex_name in selected_exercises:
            WorkoutLog.objects.create(
                user=request.user, 
                exercise=ex_name, 
                completed=True,
                calories_burned=calories_per_workout 
            )
        
        # After saving, go back to dashboard to see the progress ring fill up
        return redirect('dashboard')

    return render(request, 'workout.html', {'plan': plan, 'profile': profile})
# ---------------- PERFORMANCE ----------------
@login_required
def performance(request):
    logs = WorkoutLog.objects.filter(user=request.user).order_by('-date')
    daily_counts = defaultdict(int)
    grouped_exercises = defaultdict(list)
    
    for log in logs:
        daily_counts[log.date] += 1
        grouped_exercises[log.date].append(log.exercise)

    performance_history = []
    unique_dates = sorted(grouped_exercises.keys(), reverse=True)
    for d in unique_dates:
        performance_history.append({
            'date': d.strftime("%d %b, %Y"),
            'exercises': grouped_exercises[d],
            'score': daily_counts[d]
        })

    # Chart Data (Last 7 Days)
    chart_days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [d.strftime("%d %b") for d in chart_days]
    values = [daily_counts[d] for d in chart_days]

    # Streak Calculation
    workout_days = sorted(set(log.date for log in logs), reverse=True)
    streak = 0
    today = date.today()
    for day in workout_days:
        if day == today - timedelta(days=streak): streak += 1
        else: break

    return render(request, 'performance.html', {
        'performance_history': performance_history,
        'labels': labels,
        'values': values,
        'streak': streak,
        'workout_days_count': len(workout_days),
        'total_exercises': logs.count(),
        'avg_per_day': round(logs.count() / len(workout_days), 1) if workout_days else 0

    })

from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Session update karo taaki user logout na ho
            update_session_auth_hash(request, user)
            messages.success(request, 'Bhai, password successfully change ho gaya!')
            return redirect('profile')
        else:
            messages.error(request, 'Bhai, kuch galti hai. Details sahi se bhariye.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})