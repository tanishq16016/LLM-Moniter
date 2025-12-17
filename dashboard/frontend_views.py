"""
Frontend Views for Dashboard App

This module contains view functions for rendering HTML templates.
"""

from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

from .models import APIConfiguration
from .utils import get_available_models


@login_required(login_url='/accounts/login/')
def home(request):
    """
    Render the main dashboard home page.
    
    Displays:
    - Stats cards (requests, latency, tokens, cost, error rate)
    - Charts (token usage, latency trends, model distribution)
    - Recent traces table
    
    RBAC: Superusers see all data, regular users see only their own.
    """
    config = APIConfiguration.load()
    
    context = {
        'page_title': 'Dashboard',
        'active_page': 'home',
        'has_api_key': config.has_api_key(),
        'default_model': config.default_model,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required(login_url='/accounts/login/')
def settings_page(request):
    """
    Render the settings page.
    
    Allows:
    - API key configuration
    - Default model selection
    - Connection testing
    
    RBAC: Only superusers should see system-wide settings.
    """
    config = APIConfiguration.load()
    models = get_available_models()
    
    context = {
        'page_title': 'Settings',
        'active_page': 'settings',
        'has_api_key': config.has_api_key(),
        'is_active': config.is_active,
        'default_model': config.default_model,
        'available_models': models,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'dashboard/settings.html', context)


# Alias for URL pattern
settings = settings_page


@login_required(login_url='/accounts/login/')
def test_llm(request):
    """
    Render the LLM testing page.
    
    Provides:
    - Interactive prompt input
    - Model selection
    - Real-time response display
    - Metrics display
    """
    config = APIConfiguration.load()
    models = get_available_models()
    
    context = {
        'page_title': 'Test LLM',
        'active_page': 'test',
        'has_api_key': config.has_api_key(),
        'default_model': config.default_model,
        'available_models': models,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'dashboard/test.html', context)


@login_required(login_url='/accounts/login/')
def analytics(request):
    """
    Render the analytics page.
    
    Shows:
    - Date range selector
    - Advanced filtering
    - Detailed charts
    - Data export options
    
    RBAC: Superusers see all analytics, regular users see only their own.
    """
    config = APIConfiguration.load()
    models = get_available_models()
    
    context = {
        'page_title': 'Analytics',
        'active_page': 'analytics',
        'has_api_key': config.has_api_key(),
        'available_models': models,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'dashboard/analytics.html', context)


@login_required(login_url='/accounts/login/')
def profile(request):
    """
    Render the profile page.
    
    Allows:
    - Edit user information (first name, last name, email)
    """
    from django.contrib.auth.decorators import login_required
    from django.shortcuts import redirect
    
    # Redirect to login if not authenticated
    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/profile/')
    
    user = request.user
    
    if request.method == 'POST':
        # Update user information in auth_user table
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save(update_fields=['first_name', 'last_name', 'email'])
        
        # Redirect with success message
        return redirect('/profile/?updated=true')
    
    config = APIConfiguration.load()
    
    # Get user data from authenticated user
    user_data = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    
    context = {
        'page_title': 'Profile',
        'active_page': 'profile',
        'has_api_key': config.has_api_key(),
        'user_data': user_data,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'dashboard/profile.html', context)
