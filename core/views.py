import json
import os
import random
import requests
import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum
from datetime import date
import time
import hashlib

from .models import UserProfile, DietPlan, WorkoutPlan, WorkoutLog
from .forms import UserProfileForm, RegisterForm

# Import Production AI Pipeline
try:
    from ai_pipeline import pipeline as ai_pipeline
except ImportError:
    ai_pipeline = None


# ================================================================
# ML SETUP
# ================================================================
MODEL_DIR = os.path.join(settings.BASE_DIR, 'models')

# Demo food database — realistic responses without API
DEMO_FOODS = [
    {
        "dish_name": "Dal Chawal",
        "dish_description": "Traditional Indian lentil curry served with steamed basmati rice",
        "calories": 380, "protein_g": 14, "carbs_g": 68, "fat_g": 6,
        "fibre_g": 8, "sugar_g": 4, "sodium_mg": 420,
        "health_score": 8,
        "health_tips": "Dal chawal is a complete protein meal. Add ghee in moderation for healthy fats. Pair with salad for extra fibre."
    },
    {
        "dish_name": "Paneer Butter Masala",
        "dish_description": "Creamy tomato-based curry with soft paneer cubes and aromatic spices",
        "calories": 420, "protein_g": 18, "carbs_g": 22, "fat_g": 28,
        "fibre_g": 3, "sugar_g": 8, "sodium_mg": 680,
        "health_score": 6,
        "health_tips": "Rich in protein and calcium. Reduce butter for lower calories. Best consumed at lunch for better digestion."
    },
    {
        "dish_name": "Chicken Biryani",
        "dish_description": "Fragrant basmati rice layered with spiced chicken and caramelized onions",
        "calories": 520, "protein_g": 28, "carbs_g": 62, "fat_g": 16,
        "fibre_g": 2, "sugar_g": 3, "sodium_mg": 780,
        "health_score": 6,
        "health_tips": "High protein meal. Pair with raita for probiotics. Portion control is key — one serving is sufficient."
    },
    {
        "dish_name": "Masala Dosa",
        "dish_description": "Crispy fermented rice crepe filled with spiced potato masala",
        "calories": 340, "protein_g": 8, "carbs_g": 58, "fat_g": 10,
        "fibre_g": 4, "sugar_g": 2, "sodium_mg": 520,
        "health_score": 7,
        "health_tips": "Fermented batter aids digestion. Sambar adds protein and vegetables. Avoid excess coconut chutney to reduce fat."
    },
    {
        "dish_name": "Chole Bhature",
        "dish_description": "Spiced chickpea curry served with fluffy deep-fried bread",
        "calories": 580, "protein_g": 16, "carbs_g": 72, "fat_g": 24,
        "fibre_g": 9, "sugar_g": 5, "sodium_mg": 860,
        "health_score": 5,
        "health_tips": "Chickpeas are high in fibre and protein. Bhature is deep fried — limit to one piece. Best as occasional treat."
    },
    {
        "dish_name": "Idli Sambar",
        "dish_description": "Soft steamed rice cakes served with lentil vegetable soup",
        "calories": 280, "protein_g": 10, "carbs_g": 52, "fat_g": 4,
        "fibre_g": 6, "sugar_g": 3, "sodium_mg": 380,
        "health_score": 9,
        "health_tips": "One of the healthiest Indian breakfasts. Low fat, high protein, fermented for gut health. Excellent pre-workout meal."
    },
    {
        "dish_name": "Aloo Paratha",
        "dish_description": "Whole wheat flatbread stuffed with spiced mashed potatoes",
        "calories": 310, "protein_g": 7, "carbs_g": 48, "fat_g": 11,
        "fibre_g": 4, "sugar_g": 2, "sodium_mg": 440,
        "health_score": 6,
        "health_tips": "Use less ghee while cooking. Pair with curd for protein boost. Whole wheat provides sustained energy throughout the day."
    },
    {
        "dish_name": "Rajma Chawal",
        "dish_description": "Red kidney bean curry in tomato gravy served with steamed rice",
        "calories": 410, "protein_g": 17, "carbs_g": 72, "fat_g": 5,
        "fibre_g": 11, "sugar_g": 5, "sodium_mg": 490,
        "health_score": 9,
        "health_tips": "Excellent plant-based protein and fibre. Great for weight management. Add lemon juice for better iron absorption."
    },
]


def ml_predict_calories(age, weight, height_cm, gender, goal):
    try:
        if gender == 'male':
            bmr = 88.362 + (13.397 * weight) + (4.799 * height_cm) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height_cm) - (4.330 * age)
        tdee = bmr * 1.375
        if goal == 'loss':
            target = tdee - 500
        elif goal == 'gain':
            target = tdee + 400
        else:
            target = tdee
        return int(round(target / 50.0) * 50)
    except Exception:
        return {'loss': 1800, 'gain': 2500}.get(goal, 2200)


def ml_recommend_meals(goal, top_n=3):
    try:
        df         = joblib.load(os.path.join(MODEL_DIR, 'food_df.pkl'))
        similarity = joblib.load(os.path.join(MODEL_DIR, 'meal_similarity.pkl'))
        if goal == 'loss':
            filtered = df[(df['prep_time'] <= 30) & (df['course'] != 'dessert')]
        elif goal == 'gain':
            filtered = df[df['course'] == 'main course']
        else:
            filtered = df.copy()
        if filtered.empty:
            filtered = df.copy()
        seed_idx   = filtered.sample(1).index[0]
        sim_scores = sorted(enumerate(similarity[seed_idx]), key=lambda x: x[1], reverse=True)
        meals = []
        for idx, score in sim_scores[1:]:
            if idx >= len(df):
                continue
            row = df.iloc[idx]
            meals.append({
                'name'     : row['name'],
                'course'   : row.get('course', ''),
                'prep_time': int(row.get('prep_time', 0)),
                'score'    : round(float(score) * 100, 1),
                'reason'   : _meal_reason(row, float(score)),
            })
            if len(meals) == top_n:
                break
        return meals
    except Exception:
        return []


def _meal_reason(row, score):
    if score > 0.6:
        return "Highly matched to your goal"
    if row.get('prep_time', 99) <= 15:
        return "Super quick to prepare"
    if row.get('course') == 'main course':
        return "High energy main meal"
    return "Balanced meal option"


def ml_suggest_workout(bmi, goal):
    try:
        knn      = joblib.load(os.path.join(MODEL_DIR, 'workout_knn.pkl'))
        goal_enc = {'loss': 0, 'gain': 1, 'maintain': 2}.get(goal, 2)
        pred     = knn.predict([[bmi, goal_enc]])[0]
        return {0: 'cardio', 1: 'balanced', 2: 'strength'}.get(pred, 'balanced')
    except Exception:
        return 'balanced'


# ================================================================
# VIEWS
# ================================================================

def home(request):
    return render(request, 'home.html')


@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('profile')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if not profile.is_profile_complete:
        form = UserProfileForm(request.POST or None, instance=profile)
        if request.method == 'POST' and form.is_valid():
            p = form.save(commit=False)
            p.is_profile_complete = True
            p.save()
            return redirect('dashboard')
        return render(request, 'onboarding.html', {'form': form})
    form = UserProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('profile')
    return render(request, 'profile.html', {'form': form})


@login_required
def dashboard(request):
    profile = UserProfile.objects.get(user=request.user)
    total_inches = (profile.height_feet * 12) + profile.height_inches
    height_m     = total_inches * 0.0254
    bmi          = round(profile.weight / (height_m ** 2), 2) if height_m > 0 else 0
    if bmi < 18.5:   category = "Underweight"
    elif bmi < 25:   category = "Normal"
    elif bmi < 30:   category = "Overweight"
    else:            category = "Obese"
    height_cm   = total_inches * 2.54
    base_target = ml_predict_calories(
        age       = profile.age    or 25,
        weight    = profile.weight or 70,
        height_cm = height_cm,
        gender    = profile.gender or 'male',
        goal      = profile.goal   or 'maintain',
    )
    total_burned = WorkoutLog.objects.filter(
        user=request.user,
        date=date.today()
    ).aggregate(total=Sum('calories_burned'))['total'] or 0
    remaining_calories = max(0, base_target - total_burned)
    ml_meals        = ml_recommend_meals(goal=profile.goal or 'maintain', top_n=3)
    ml_workout_type = ml_suggest_workout(bmi=bmi, goal=profile.goal or 'maintain')
    return render(request, 'dashboard.html', {
        'profile'         : profile,
        'bmi'             : bmi,
        'category'        : category,
        'calories'        : remaining_calories,
        'base_target'     : base_target,
        'total_burned'    : total_burned,
        'ml_meals'        : ml_meals,
        'ml_workout_type' : ml_workout_type,
    })


@login_required
def diet(request):
    profile = UserProfile.objects.get(user=request.user)
    plan    = DietPlan.objects.filter(goal=profile.goal).first()
    return render(request, 'diet.html', {'plan': plan})


@login_required
def workout(request):
    profile = UserProfile.objects.get(user=request.user)
    plan    = WorkoutPlan.objects.filter(goal=profile.goal).first()
    if request.method == 'POST':
        for ex in request.POST.getlist('exercise'):
            WorkoutLog.objects.create(
                user            = request.user,
                exercise        = ex,
                calories_burned = 200
            )
        return redirect('dashboard')
    return render(request, 'workout.html', {'plan': plan})


@login_required
def performance(request):
    logs = WorkoutLog.objects.filter(user=request.user)
    return render(request, 'performance.html', {'logs': logs})


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Password updated")
        return redirect('profile')
    return render(request, 'change_password.html', {'form': form})


# ================================================================
# FOOD PHOTO ANALYZER — Smart Demo Mode (No API needed)
# ================================================================

@login_required
def food_scan(request):
    return render(request, 'food_scan.html')


@login_required
@require_POST
def analyze_food_api(request):
    """
    Advanced AI Image Analysis — Identifies food, counts calories, and assesses health.
    Uses a custom vision model with feature extraction.
    """
    try:
        body = json.loads(request.body)
        image_base64 = body.get('image_base64')
        
        if not image_base64:
            return JsonResponse({'error': 'No image received'}, status=400)

        # Use the Production-Grade AI Pipeline (YOLOv8 + EfficientNet + Dynamic Portion)
        if ai_pipeline:
            profile = UserProfile.objects.get(user=request.user)
            result = ai_pipeline.run(image_base64, profile)
            
            if not result:
                return JsonResponse({'error': 'Neural pipeline could not segment the food. Please ensure the plate is clearly visible.'}, status=400)
            
            # Map pipeline result to UI format
            ui_response = {
                'dish_name': result['food'],
                'calories': result['calories'],
                'protein_g': result['protein_g'],
                'carbs_g': result['carbs_g'],
                'fat_g': result['fat_g'],
                'health_score': 8 if result['calories'] < 500 else 4,
                'is_healthy_status': result['calories'] < 600,
                'model_info': result['model_stack'],
                'health_tips': result['nlp_reasoning'],
                'meta': {
                    'portion_factor': result['segmentation_score'],
                    'est_weight_g': result['estimated_weight_g']
                }
            }
            
            return JsonResponse(ui_response)
        else:
            return JsonResponse({'error': 'Production AI Pipeline not initialized.'}, status=500)

    except Exception as e:
        return JsonResponse({'error': f'AI Engine Error: {str(e)}'}, status=500)


@login_required
@require_POST
def log_food_scan(request):
    from .models import DailyStats
    from datetime import date as today_date
    try:
        dish_name = request.POST.get('dish_name', 'Scanned Food')
        calories  = int(request.POST.get('calories', 0))
        stats, _ = DailyStats.objects.get_or_create(
            user=request.user,
            date=today_date.today()
        )
        stats.calories_consumed = (stats.calories_consumed or 0) + calories
        stats.save()
        messages.success(request, f"✅ {dish_name} ({calories} kcal) logged!")
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f"Log nahi hua: {e}")
        return redirect('food_scan')