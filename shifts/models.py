from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    #BOA Levels
    BOA_CHOICES = [
        (1, "BOA1"),
        (2, "BOA2"),
        (3, "BOA3"),
        (4, "BOA4"),
    ]
    boa_level = models.IntegerField(choices=BOA_CHOICES, default=1)

class Shift(models.Model):
    SHIFT_TYPES = [('DESK', 'Desk Shift'), ('ROAMER', 'Roamer Shift'), ('OPS_LEAD', 'Ops Lead Shift')]

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=100)
    shift_type = models.CharField(max_length=10, choices=SHIFT_TYPES)
    capacity = models.PositiveIntegerField(default=3)

class Signup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='signups')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'shift')