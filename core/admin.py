from django.contrib import admin
from .models import UserProfile, WorkoutLog, TrainingImage

# Define custom admin site for NutriScan
class NutriScanAdminSite(admin.AdminSite):
    site_header = "NutriScan AI Command Center"
    site_title = "NutriScan Admin"
    index_title = "Welcome to the Neural Engine Dashboard"

admin_site = NutriScanAdminSite(name='nutriscan_admin')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'weight', 'goal', 'is_profile_complete')
    search_fields = ('user__username', 'goal')

class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'exercise', 'calories_burned', 'date')
    list_filter = ('date', 'exercise')

class TrainingImageAdmin(admin.ModelAdmin):
    list_display = ('label', 'id', 'created_at')
    list_filter = ('label',)
    search_fields = ('label',)

from django.contrib.auth.models import User, Group

# Register with custom site
admin_site.register(User)
admin_site.register(Group)
admin_site.register(UserProfile, UserProfileAdmin)
admin_site.register(WorkoutLog, WorkoutLogAdmin)
admin_site.register(TrainingImage, TrainingImageAdmin)
