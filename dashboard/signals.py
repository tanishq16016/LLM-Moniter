"""
Signal handlers for authentication events
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib import messages
from django.dispatch import receiver
from allauth.account.signals import user_signed_up


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    """Show success message when user logs in - skip if just registered"""
    # Check if user just signed up (flag set by signup signal)
    just_signed_up = request.session.pop('just_signed_up', False)
    if not just_signed_up:
        messages.success(request, f'Welcome back, {user.username}!')


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    """Show success message when user logs out"""
    messages.success(request, 'You have been logged out successfully.')


@receiver(user_signed_up)
def on_user_signed_up(sender, request, user, **kwargs):
    """Show success message when user signs up"""
    messages.success(request, f'Account created successfully! Welcome {user.username}, please sign in.')
    # Set flag to skip welcome message on next login
    request.session['just_signed_up'] = True
