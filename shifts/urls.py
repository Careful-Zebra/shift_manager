from django.urls import path
from . import views

urlpatterns = [
    #main dashboard page
    path('', views.dashboard, name='dashboard'),

    #the url that the claim button triggers
    path('claim/<int:shift_id>/', views.claim_shift, name='claim_shift'),
]