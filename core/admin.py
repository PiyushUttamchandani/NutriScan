from django.contrib import admin
from .models import UserProfile
from .models import DietPlan
from .models import WorkoutPlan
from .models import WorkoutLog

admin.site.register(WorkoutLog)

admin.site.register(WorkoutPlan)

admin.site.register(DietPlan)

admin.site.register(UserProfile)