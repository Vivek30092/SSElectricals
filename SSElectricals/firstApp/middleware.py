from django.utils import timezone
from .models import AdminSession, AdminActivityLog
from django.contrib.sessions.models import Session

class AdminSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            session_key = request.session.session_key
            if session_key:
                # Update last activity
                AdminSession.objects.filter(session_key=session_key).update(last_activity=timezone.now())
                
                # Check if session exists, create if not (e.g. fresh login)
                if not AdminSession.objects.filter(session_key=session_key).exists():
                     # Get client IP
                    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                    if x_forwarded_for:
                        ip = x_forwarded_for.split(',')[0]
                    else:
                        ip = request.META.get('REMOTE_ADDR')
                        
                    AdminSession.objects.create(
                        user=request.user,
                        session_key=session_key,
                        ip_address=ip,
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
                    )

        response = self.get_response(request)
        return response

class AdminActivityLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # This middleware might be intended to log specific actions based on views or signals.
        # For a simple middleware hook, we might just track that a request happened, 
        # but typically activity logging is better done in views or via signals.
        # However, since it's listed in middleware, it might be looking for specific attributes set on the request 
        # during view processing, or just logging every admin request (which is noisy).
        
        # Given the previous context, we'll keep it simple: pass through.
        # Logic for logging specific actions (creation/updates) is usually in signals or views.
        # If we need to log 'Login' or 'Logout' specifically, signals are better, 
        # but maybe this middleware checks for successful login/logout in the response?
        
        response = self.get_response(request)
        return response
