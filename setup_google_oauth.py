"""
One-time script to setup Google OAuth in production database
Run this locally but it connects to your Neon production database
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'llm_monitor.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def setup_google_oauth():
    print('Setting up Google OAuth...')
    
    # Get credentials
    client_id = input('Enter Google OAuth Client ID: ').strip()
    client_secret = input('Enter Google OAuth Client Secret: ').strip()
    
    if not client_id or not client_secret:
        print('Error: Both Client ID and Secret are required')
        return
    
    # Delete existing Google apps
    deleted_count, _ = SocialApp.objects.filter(provider='google').delete()
    print(f'Deleted {deleted_count} existing Google OAuth apps')
    
    # Get or create the site for your production domain
    site, created = Site.objects.get_or_create(
        domain='llm-moniter.vercel.app',
        defaults={'name': 'LLM Monitor'}
    )
    if created:
        print(f'Created new site: {site.domain}')
    else:
        print(f'Using existing site: {site.domain}')
    
    # Create new Google app
    app = SocialApp.objects.create(
        provider='google',
        name='Google',
        client_id=client_id,
        secret=client_secret
    )
    app.sites.add(site)
    
    print(f'✓ Created Google OAuth app (ID: {app.id})')
    print(f'✓ Associated with site: {site.domain}')
    print('\n✅ Google OAuth setup complete!')
    print('\nMake sure your Google Cloud Console has these authorized redirect URIs:')
    print(f'  https://{site.domain}/accounts/google/login/callback/')

if __name__ == '__main__':
    setup_google_oauth()
