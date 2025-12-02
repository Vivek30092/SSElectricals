from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from datetime import timedelta
from .models import AdminSession, AdminActivityLog


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AdminSessionMiddleware(MiddlewareMixin):
    """
    Middleware to track admin sessions and auto-logout after inactivity.
    """
    
    def process_request(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            session_key = request.session.session_key
            
            if session_key:
                try:
                    admin_session = AdminSession.objects.get(
                        session_key=session_key,
                        is_active=True
                    )
                    
                    # Check for inactivity timeout (30 minutes)
                    timeout_duration = timedelta(minutes=30)
                    time_since_activity = timezone.now() - admin_session.last_activity
                    
                    if time_since_activity > timeout_duration:
                        # Auto-logout due to inactivity
                        admin_session.is_active = False
                        admin_session.logout_time = timezone.now()
                        admin_session.save()
                        
                        # Log the auto-logout
                        AdminActivityLog.objects.create(
                            admin=request.user,
                            action='LOGOUT',
                            module='SESSION',
                            description='Auto-logout due to inactivity',
                            ip_address=get_client_ip(request)
                        )
                        
                        # Force Django logout
                        from django.contrib.auth import logout
                        logout(request)
                        return None
                    
                    # Update last activity
                    admin_session.last_activity = timezone.now()
                    admin_session.save(update_fields=['last_activity'])
                    
                except AdminSession.DoesNotExist:
                    pass
        
        return None


class AdminActivityLogMiddleware(MiddlewareMixin):
    """
    Middleware to log admin activities automatically and attach user info to models.
    """
    
    def process_request(self, request):
        """Attach current user and IP to request for signal handlers."""
        if request.user.is_authenticated and request.user.is_staff:
            # Store user and IP in thread local or request
            request._current_user = request.user
            request._ip_address = get_client_ip(request)
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Attach user and IP to models being saved in admin."""
        if request.user.is_authenticated and request.user.is_staff:
            # This will be used by ModelAdmin save_model method
            if hasattr(request, 'POST') and request.method == 'POST':
                from django.contrib.admin.options import ModelAdmin
                
                # Monkey patch to attach user to model instances
                original_save_model = ModelAdmin.save_model
                
                def patched_save_model(self, request, obj, form, change):
                    obj._current_user = request.user
                    obj._ip_address = get_client_ip(request)
                    return original_save_model(self, request, obj, form, change)
                
                ModelAdmin.save_model = patched_save_model
        
        return None
    
    def process_response(self, request, response):
        if request.user.is_authenticated and request.user.is_staff:
            # Log admin panel actions (legacy fallback for non-signal actions)
            if request.path.startswith('/admin/') and request.method in ['POST', 'DELETE']:
                # Determine action and module from request path
                path_parts = request.path.split('/')
                
                action = None
                module = None
                description = ''
                
                # Parse the admin URL to determine action and module
                if 'add' in request.path:
                    action = 'CREATE'
                elif 'delete' in request.path:
                    action = 'DELETE'
                elif 'change' in request.path:
                    action = 'UPDATE'
                
                # Determine module from path
                if 'product' in request.path.lower():
                    module = 'PRODUCT'
                elif 'category' in request.path.lower():
                    module = 'CATEGORY'
                elif 'order' in request.path.lower():
                    module = 'ORDER'
                elif 'user' in request.path.lower() or 'customuser' in request.path.lower():
                    module = 'USER'
                elif 'cart' in request.path.lower():
                    module = 'CART'
                
                # Note: Signals will handle most logging now, this is just a fallback
                # for any actions not caught by signals
        
        return response
