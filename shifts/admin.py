from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Shift, Signup, User

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'boa_level', 'is_staff')

    #adds custom boa_level to edit screen
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('boa_level',)}),
    )

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('shift_type', 'start_time', 'location', 'capacity')
    list_filter = ('shift_type', 'start_time', 'location')


#registering signups so we can see them in admin
@admin.register(Signup)
class SignupAdmin(admin.ModelAdmin):
    list_display = ('user', 'shift', 'timestamp')
