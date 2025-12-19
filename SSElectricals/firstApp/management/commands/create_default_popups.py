from django.core.management.base import BaseCommand
from firstApp.models import LoginPopup, CustomUser


class Command(BaseCommand):
    help = 'Create default login popups for testing notice and free delivery offer'

    def handle(self, *args, **kwargs):
        # Get first admin user as creator
        admin_user = CustomUser.objects.filter(is_staff=True).first()
        
        if not admin_user:
            self.stdout.write(self.style.WARNING('No admin user found. Please create one first.'))
            return

        # Create Center Modal - Testing Notice
        center_modal, created = LoginPopup.objects.get_or_create(
            popup_type='CENTER_MODAL',
            defaults={
                'title': 'Testing Phase',
                'message': 'This application is currently in testing phase. If you face any glitch or find any bug, please help us improve by sending a detailed email with proof to: <strong>vivekkumarc934@gmail.com</strong>',
                'is_enabled': True,
                'auto_hide_seconds': 0,  # Manual close only
                'created_by': admin_user
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created CENTER_MODAL popup (Testing Notice)'))
        else:
            self.stdout.write(self.style.WARNING('CENTER_MODAL popup already exists'))

        # Create Bottom Right Card - Free Delivery Offer
        bottom_right, created = LoginPopup.objects.get_or_create(
            popup_type='BOTTOM_RIGHT',
            defaults={
                'title': 'Special Offer! 🎁',
                'message': 'You will get <strong>free delivery*</strong> on your first order<br><small class="text-muted">*Terms and conditions apply</small>',
                'is_enabled': True,
                'auto_hide_seconds': 10,  # Auto-hide after 10 seconds
                'created_by': admin_user
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created BOTTOM_RIGHT popup (Free Delivery Offer)'))
        else:
            self.stdout.write(self.style.WARNING('BOTTOM_RIGHT popup already exists'))

        self.stdout.write(self.style.SUCCESS('\nDefault login popups setup complete!'))
        self.stdout.write(self.style.SUCCESS('Users will see these popups when they log in.'))
        self.stdout.write(self.style.SUCCESS('You can manage them in Admin Panel > Login Popups'))
