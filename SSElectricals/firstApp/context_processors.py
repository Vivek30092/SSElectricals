"""
Context processors for firstApp.
Makes certain data available to all templates.
"""
from .models import SiteAnnouncement


def site_announcements(request):
    """
    Adds active site announcements to the template context.
    """
    user = request.user if hasattr(request, 'user') else None
    announcements = SiteAnnouncement.get_active_announcements(user)
    
    # Separate by position
    center_announcements = announcements.filter(position__in=['center', 'both'])
    toast_announcements = announcements.filter(position__in=['bottom_right', 'both'])
    
    return {
        'site_announcements': announcements,
        'center_announcements': center_announcements,
        'toast_announcements': toast_announcements,
    }
