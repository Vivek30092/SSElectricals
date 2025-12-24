from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle login/signup redirects
    """
    
    def is_open_for_signup(self, request):
        """
        Allow signups
        """
        return True
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Force auto-signup for all social accounts (Google)
        This skips the signup confirmation form
        """
        return True
    
    def get_login_redirect_url(self, request):
        """
        Redirect after login
        """
        # Check if user is staff/admin
        if request.user.is_staff:
            return '/shop-admin/dashboard/'
        return '/'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to handle Google OAuth users
    Redirects new Google users to profile page to complete their information
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a social provider,
        but before the login is actually processed.
        
        Auto-connect Google account to existing account if email matches.
        """
        # If user is already logged in, skip the Google login
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in!")
            # We cannot redirect here, but we can mark it for later
            request.session['already_logged_in'] = True
            return
        
        # Check if a user with this email already exists
        if sociallogin.account.provider == 'google':
            try:
                email = sociallogin.account.extra_data.get('email')
                if email:
                    from .models import CustomUser
                    # Try to find existing user with this email
                    try:
                        user = CustomUser.objects.get(email=email)
                        # Auto-connect the social account to existing user
                        sociallogin.connect(request, user)
                        logger.info(f"Auto-connected Google account to existing user: {email}")
                    except CustomUser.DoesNotExist:
                        # No existing user, will create new account
                        logger.info(f"No existing user found for {email}, will create new account")
                        pass
            except Exception as e:
                logger.error(f"Error in pre_social_login: {e}")
                pass
    
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
        
        # Check if this was an "already logged in" situation
        if request.session.get('already_logged_in'):
            del request.session['already_logged_in']
            return '/'
        
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
