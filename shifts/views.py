from django.contrib import messages
from django.views.decorators.cache import never_cache

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from collections import defaultdict
from .models import Shift, Signup, User
from django.utils import timezone
import datetime

# Create your views here.

@login_required
def home(request):
    #renders page w/ links to 4 schedules (finals ops, finals non-ops, rrr ops, rrr non-ops)
    return render(request, 'shifts/home.html')

@login_required
@never_cache
def schedule_view(request, week_type, role_type):
    #start w/ all shifts sorted
    shifts = Shift.objects.all().order_by('start_time')
    target_datetime = datetime.datetime(2026, 5, 10) #start of finals week, change in future semesters

    #filter by week type
    if week_type == 'rrr':
        shifts = shifts.filter(start_time__lt=target_datetime)
        page_title = "RRR Week Schedule"
    elif week_type == 'finals':
        shifts = shifts.filter(start_time__gte=target_datetime)
        page_title = "Finals Week Schedule"
    else:
        return HttpResponse("Invalid week type.", status=400)
    
    #filter by role type
    if role_type == 'desk_roamer':
        shifts = shifts.exclude(shift_type='OPS_LEAD')
        page_title += " (Desk & Roamer)"
    elif role_type == 'ops_lead':
        shifts = shifts.filter(shift_type='OPS_LEAD')
        page_title += " (Ops Lead)"
    else:
        return HttpResponse("Invalid role type.", status=400)
    
    user_shifts = Signup.objects.filter(user=request.user).values_list('shift_id', flat=True)
    user_shift_count = len(user_shifts)
    
    max_shifts = 3 if request.user.boa_level in [1, 2] else 2 #lowk irrelevant
    max_shifts_finals = 2
    max_shifts_rrr = 3
    
    # Calculate user's specific counts
    user_finals_count = Signup.objects.filter(user=request.user, shift__start_time__gte=target_datetime).count()
    user_rrr_count = Signup.objects.filter(user=request.user, shift__start_time__lt=target_datetime).count()

    dates = sorted(list(set(shift.start_time.date() for shift in shifts)))

    temp_schedule = defaultdict(lambda: defaultdict(list))
    for shift in shifts:
        s_type = shift.get_shift_type_display()
        date = shift.start_time.date()
        temp_schedule[s_type][date].append(shift)

    schedule = {}
    for s_type, dates_dict in temp_schedule.items():
        schedule[s_type] = []
        for date in dates:
            schedule[s_type].append(dates_dict.get(date, []))

    return render(request, 'shifts/dashboard.html', {
        'schedule': schedule,
        'dates': dates,
        'user_shifts': user_shifts,
        'user_shift_count': user_shift_count, 
        'max_shifts': max_shifts,
        'max_shifts_finals': max_shifts_finals,
        'max_shifts_rrr': max_shifts_rrr,
        'user_finals_count': user_finals_count,
        'user_rrr_count': user_rrr_count,
        'page_title': page_title # Pass the title so the template knows what we are looking at
    })

@login_required
def claim_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    user = request.user

    past_webpage = request.META.get('HTTP_REFERER', '')

    #0. check if user already signed up for this shift
    existing_signup = Signup.objects.filter(user=user, shift=shift).first()
    if existing_signup:
        existing_signup.delete() #if so, remove it and let them try again (allows them to "unclaim" if they clicked by accident)
        return redirect(past_webpage)

    #1. permission check
    if user.boa_level in [1, 2] and shift.shift_type == 'OPS_LEAD':
        return HttpResponse("You do not have the BOA Level required for this shift.", status=403)
    if user.boa_level == 3 and shift.shift_type != 'OPS_LEAD':
        return HttpResponse("Please only request Ops lead shifts for now.", status=403)
    
    max_shifts_finals = 2
    max_shifts_rrr = 3
    # Count how many shifts they are currently signed up for
    current_shift_count = Signup.objects.filter(user=user).count()

    # Define the timezone-aware cutoff date for finals week
    target_datetime = timezone.make_aware(datetime.datetime(2026, 5, 10))

    # Use it for database filters
    user_finals_count = Signup.objects.filter(user=user, shift__start_time__gte=target_datetime).count()
    user_rrr_count = Signup.objects.filter(user=user, shift__start_time__lt=target_datetime).count()

    # Use it to check the current shift they are trying to claim
    if user_finals_count >= max_shifts_finals and shift.start_time >= target_datetime:
        return HttpResponse(f"You have reached your maximum limit of {max_shifts_finals} finals week shifts.", status=403)
        
    if user_rrr_count >= max_shifts_rrr and shift.start_time < target_datetime:
        return HttpResponse(f"You have reached your maximum limit of {max_shifts_rrr} RRR week shifts.", status=403)

    

    #2. capacity check (atomic transac)
    with transaction.atomic():
        # LOCK the shift row for this specific transaction
        locked_shift = Shift.objects.select_for_update().get(id=shift.id)
        
        # Check signups against the locked shift
        current_signups = Signup.objects.filter(shift=locked_shift).count()
        
        if current_signups < locked_shift.capacity:
            # good, create the signup
            Signup.objects.create(user=user, shift=locked_shift)
        else:
            # return HttpResponse("This shift is already full.", status=400)
            messages.error(request, "Sorry, someone just grabbed that shift right before you!")

    return redirect(past_webpage) #redirect back to where they came from (either finals or rrr schedule page)

# @login_required
# def dashboard(request):
#     # Grab all shifts, sorted chronologically (earliest to latest stacking)
#     all_shifts = Shift.objects.all().order_by('start_time')
#     user_shifts = Signup.objects.filter(user=request.user).values_list('shift_id', flat=True)

#     # Get dates for table column headers
#     dates = sorted(list(set(shift.start_time.date() for shift in all_shifts)))

#     # Calculate max limits and current counts to show on the dashboard
#     user_shift_count = len(user_shifts)
#     max_shifts = 3 if request.user.boa_level in [1, 2] else 2
#     max_shifts_finals = 2
#     max_shifts_rrr = 3
#     user_finals_count = 0
#     user_rrr_count = 0
#     # Creates a timezone-aware datetime object for midnight on May 10, 2026
#     target_datetime = datetime.datetime(2026, 5, 10)

#     user_rrr_count = Signup.objects.filter(
#         user=request.user, 
#         shift__start_time__lt=target_datetime
#     ).count()    
#     user_finals_count = user_shift_count - user_rrr_count
    

#     # 1. Group shifts by Type and Date dynamically
#     temp_schedule = defaultdict(lambda: defaultdict(list))
#     for shift in all_shifts:
#         shift_type = shift.get_shift_type_display()
#         date = shift.start_time.date()
#         temp_schedule[shift_type][date].append(shift)

#     # 2. Format into clean columns matching the 'dates' list for the template
#     schedule = {}
#     for shift_type, dates_dict in temp_schedule.items():
#         schedule[shift_type] = []
#         for date in dates:
#             # We just append the list of shifts for each day (left-to-right columns)
#             schedule[shift_type].append(dates_dict.get(date, []))

#     return render(request, 'shifts/dashboard.html', 
#                   {'schedule': schedule,
#                    'dates': dates,
#                    'user_shifts': user_shifts,
#                    'user_shift_count': user_shift_count, 
#                    'max_shifts_finals': max_shifts_finals,
#                    'max_shifts_rrr': max_shifts_rrr,
#                    'user_finals_count': user_finals_count,
#                    'user_rrr_count': user_rrr_count,})