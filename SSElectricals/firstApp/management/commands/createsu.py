import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Automatically create a superuser for Render deployment'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Read credentials from environment variables
        username = os.environ.get('DJANGO_SU_NAME')
        email = os.environ.get('DJANGO_SU_EMAIL')
        password = os.environ.get('DJANGO_SU_PASSWORD')

        # Validate that all required environment variables are present
        if not all([username, email, password]):
            self.stderr.write(self.style.ERROR(
                'Missing required environment variables for superuser creation.\n'
                'Please set DJANGO_SU_NAME, DJANGO_SU_EMAIL, and DJANGO_SU_PASSWORD.'
            ))
            return

        # Check if the user already exists by email or username
        user_exists = User.objects.filter(email=email).exists() or \
                      User.objects.filter(username=username).exists()

        if not user_exists:
            self.stdout.write(f'🚀 Creating superuser: {username} ({email})...')
            try:
                # Create the superuser
                # Note: We provide both email and username as CustomUser requires both
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Set role to 'ADMIN' as per CustomUser model choice
                if hasattr(user, 'role'):
                    user.role = 'ADMIN'
                    user.save()
                    
                self.stdout.write(self.style.SUCCESS(f'✅ Successfully created superuser: {username}'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'❌ Error creating superuser: {e}'))
        else:
            self.stdout.write(self.style.WARNING(f'ℹ️ Superuser with email "{email}" or username "{username}" already exists. Skipping creation.'))
