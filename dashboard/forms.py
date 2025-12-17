"""
Custom allauth forms to include first_name and last_name
"""
from allauth.account.forms import SignupForm
from allauth.account.adapter import DefaultAccountAdapter
from django import forms
from django.contrib.auth import logout


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter to redirect to login after signup and prevent auto-login"""
    
    def login(self, request, user):
        """Override to prevent auto-login after signup"""
        # Check if this is during signup process (not a regular login)
        if request.path == '/accounts/signup/':
            # Don't login, just return
            return
        # For regular login, call parent
        super().login(request, user)
    
    def get_signup_redirect_url(self, request):
        """Redirect to login page after signup"""
        return '/accounts/login/'


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()
        return user
