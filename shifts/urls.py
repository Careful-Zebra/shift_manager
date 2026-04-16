from django.urls import path
from . import views

urlpatterns = [
    #landing page w/ 4 links
    path('', views.home, name='home'),

    path('schedule/<str:week_type>/<str:role_type>/', views.schedule_view, name='schedule_view'),

    #the url that the claim button triggers
    path('claim/<int:shift_id>/', views.claim_shift, name='claim_shift'),
]