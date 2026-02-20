from django.contrib.auth.models import User
from django.db import models

class DietPlan(models.Model):

    goal = models.CharField(
        max_length=20,
        choices=[
            ('loss','Weight Loss'),
            ('gain','Weight Gain'),
            ('maintain','Maintain')
        ]
    )

    breakfast = models.TextField()
    lunch = models.TextField()
    dinner = models.TextField()

    def __str__(self):
        return self.goal

#---------- UserProfile ----------

class UserProfile(models.Model):

    # -------- USER LINK --------
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # -------- PERSONAL DETAILS --------
    age = models.PositiveIntegerField(null=True, blank=True)
    height_feet = models.PositiveIntegerField(null=True, blank=True)
    height_inches = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)

    gender = models.CharField(
        max_length=10,
        choices=[
            ('male','Male'),
            ('female','Female'),
            ('other','Other')
        ],
        null=True,
        blank=True
    )

    goal = models.CharField(
        max_length=20,
        choices=[
            ('loss','Weight Loss'),
            ('gain','Weight Gain'),
            ('maintain','Maintain')
        ],
        null=True,
        blank=True
    )

    # -------- PROFILE STATUS --------
    is_profile_complete = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
class WorkoutPlan(models.Model):

    goal = models.CharField(
        max_length=20,
        choices=[
            ('loss','Weight Loss'),
            ('gain','Weight Gain'),
            ('maintain','Maintain')
        ]
    )

    exercise_1 = models.CharField(max_length=100)
    exercise_2 = models.CharField(max_length=100)
    exercise_3 = models.CharField(max_length=100)

    def __str__(self):
        return self.goal
    
class WorkoutLog(models.Model):

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    exercise = models.CharField(max_length=100)
    completed = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.exercise}"