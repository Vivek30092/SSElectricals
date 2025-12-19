from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.contrib import messages
import logging

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to handle Google OAuth users
    Redirects new Google users to profile page to complete their information
    """
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user data from social account
        """
        user = super().populate_user(request, sociallogin, data)
        
        logger.info(f"Google login for email: {user.email}")
        
        # Ensure username is set and unique
        if not user.username:
            base_username = user.email.split('@')[0]
            user.username = base_username
            
            # Make username unique if needed
            from .models import CustomUser
            counter = 1
            while CustomUser.objects.filter(username=user.username).exists():
                user.username = f"{base_username}{counter}"
                counter += 1
            
            logger.info(f"Generated username: {user.username}")
        
        return user
    
    def get_login_redirect_url(self, request):
        """
        Redirect Google users to profile page if they don't have a phone number
        Also set login popup flag for all Google OAuth logins
        """
        user = request.user
        
        # Set the login popup flag for Google OAuth users
        if user.is_authenticated:
            request.session['show_login_popups'] = True
            logger.info(f"Set show_login_popups=True for Google user: {user.email}")
        
        # Check if user logged in via Google and doesn't have phone number
        if user.is_authenticated and not user.phone_number:
            messages.info(
                request,
                "Welcome! Please complete your profile by adding your phone number."
            )
            return '/profile/'
        
        # Default redirect for users with complete profiles
        return super().get_login_redirect_url(request)
