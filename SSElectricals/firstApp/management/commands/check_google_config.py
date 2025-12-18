"""
Management command to check and fix Site and SocialApp configuration
Run with: python manage.py check_google_config
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Check Google OAuth configuration and fix common issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Checking Google OAuth Configuration ===\n'))
        
        # Check Sites
        sites = Site.objects.all()
        self.stdout.write(f'Total Sites: {sites.count()}')
        for site in sites:
            self.stdout.write(f'  - ID: {site.id}, Domain: {site.domain}, Name: {site.name}')
        
        # Check Google Apps
        google_apps = SocialApp.objects.filter(provider='google')
        self.stdout.write(f'\nTotal Google Apps: {google_apps.count()}')
        for app in google_apps:
            self.stdout.write(f'  - Name: {app.name}')
            self.stdout.write(f'    Client ID: {app.client_id[:30]}...')
            self.stdout.write(f'    Sites: {", ".join([s.domain for s in app.sites.all()])}')
        
        # Check for issues
        if google_apps.count() > 1:
            self.stdout.write(self.style.WARNING('\n⚠ ISSUE: Multiple Google apps found!'))
            self.stdout.write('Run: python manage.py cleanup_google_apps')
        
        if google_apps.count() == 1:
            app = google_apps.first()
            if app.sites.count() == 0:
                self.stdout.write(self.style.WARNING('\n⚠ ISSUE: Google app not linked to any site!'))
                self.stdout.write('Fix: Add a site to the Google app in admin')
            
            if app.sites.count() > 1:
                self.stdout.write(self.style.WARNING(f'\n⚠ ISSUE: Google app linked to {app.sites.count()} sites!'))
                self.stdout.write('This might cause issues. Keep only one site.')
        
        if google_apps.count() == 0:
            self.stdout.write(self.style.ERROR('\n✗ ERROR: No Google app configured!'))
            self.stdout.write('Create one in admin at /admin/socialaccount/socialapp/add/')
        
        self.stdout.write(self.style.SUCCESS('\n✓ Check complete!'))
