"""
Management command to clean up duplicate Google Social Applications
Run with: python manage.py cleanup_google_apps
"""
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Remove duplicate Google Social Applications, keeping only the first one'

    def handle(self, *args, **options):
        google_apps = SocialApp.objects.filter(provider='google')
        count = google_apps.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No Google Social Applications found'))
            return
        
        if count == 1:
            self.stdout.write(self.style.SUCCESS('Only one Google app found - no cleanup needed!'))
            app = google_apps.first()
            self.stdout.write(f'App name: {app.name}')
            self.stdout.write(f'Client ID: {app.client_id[:20]}...')
            return
        
        # Multiple apps found - show them
        self.stdout.write(self.style.WARNING(f'Found {count} Google Social Applications:'))
        for i, app in enumerate(google_apps, 1):
            self.stdout.write(f'{i}. Name: {app.name}, Client ID: {app.client_id[:20]}...')
        
        # Keep the first one, delete the rest
        first_app = google_apps.first()
        duplicates = google_apps.exclude(id=first_app.id)
        deleted_count = duplicates.count()
        
        self.stdout.write(f'\nKeeping: {first_app.name}')
        duplicates.delete()
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully deleted {deleted_count} duplicate Google app(s)'))
        self.stdout.write(self.style.SUCCESS('Google OAuth should now work correctly!'))
