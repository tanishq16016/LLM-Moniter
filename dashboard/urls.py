"""
Frontend URL Configuration for Dashboard App

This module contains URL patterns for the frontend views (HTML pages).
"""

from django.urls import path
from . import frontend_views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home page
    path('', frontend_views.home, name='home'),
    
    # Settings page
    path('settings/', frontend_views.settings, name='settings'),
    
    # Test LLM page
    path('test/', frontend_views.test_llm, name='test'),
    
    # Analytics page
    path('analytics/', frontend_views.analytics, name='analytics'),
    
    # Profile page
    path('profile/', frontend_views.profile, name='profile'),
]
