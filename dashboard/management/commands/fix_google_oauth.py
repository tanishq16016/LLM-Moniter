"""
Management command to fix Google OAuth configuration
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Fix Google OAuth configuration by ensuring single SocialApp'

    def handle(self, *args, **options):
        self.stdout.write('Checking Google OAuth configuration...')
        
        # Show all sites
        sites = Site.objects.all()
        self.stdout.write(f'\nSites in database: {sites.count()}')
        for site in sites:
            self.stdout.write(f'  - {site.id}: {site.domain} (name: {site.name})')
        
        # Show all Google apps
        google_apps = SocialApp.objects.filter(provider='google')
        self.stdout.write(f'\nGoogle SocialApps: {google_apps.count()}')
        for app in google_apps:
            app_sites = app.sites.all()
            self.stdout.write(f'  - ID {app.id}: {app.name}')
            self.stdout.write(f'    Client ID: {app.client_id[:40]}...')
            self.stdout.write(f'    Sites: {[s.domain for s in app_sites]}')
        
        # Delete all Google apps
        self.stdout.write('\nDeleting all Google OAuth apps...')
        deleted_count, _ = SocialApp.objects.filter(provider='google').delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} apps'))
        
        # Create new Google app with credentials from environment or user input
        self.stdout.write('\nCreating new Google OAuth app...')
        
        # Get credentials from environment or prompt
        import os
        client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', input('Enter Google OAuth Client ID: '))
        client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', input('Enter Google OAuth Client Secret: '))
        
        app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id=client_id,
            secret=client_secret
        )
        
        # Add to current site
        current_site = Site.objects.get_current()
        app.sites.add(current_site)
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created Google OAuth app (ID: {app.id})'))
        self.stdout.write(self.style.SUCCESS(f'✓ Associated with site: {current_site.domain}'))
        self.stdout.write(self.style.SUCCESS('\nGoogle OAuth configuration fixed!'))
