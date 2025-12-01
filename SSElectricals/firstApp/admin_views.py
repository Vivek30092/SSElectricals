from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import Product, Order, OrderItem, AdminSession, AdminActivityLog, Category, CustomUser


def superuser_required(user):
    return user.is_superuser


@staff_member_required
def admin_dashboard(request):
    """
    Custom admin dashboard with metrics, charts, and session management.
    """
    # Calculate metrics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='Delivered').aggregate(
        total=Sum('total_price')
    )['total'] or 0
    
    # Orders by status
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Active admin sessions
    active_sessions = AdminSession.objects.filter(
        is_active=True
    ).select_related('user').order_by('-last_activity')
    
    # Sales data for charts (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_sales = Order.objects.filter(
        created_at__gte=thirty_days_ago,
        status='Delivered'
    ).extra(
        select={'day': 'DATE(created_at)'}
    ).values('day').annotate(
        total=Sum('total_price'),
        count=Count('id')
    ).order_by('day')
    
    # Prepare chart data
    chart_labels = [item['day'].strftime('%Y-%m-%d') for item in daily_sales]
    chart_data = [float(item['total']) for item in daily_sales]
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'orders_by_status': orders_by_status,
        'recent_orders': recent_orders,
        'active_sessions': active_sessions,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    
    return render(request, 'admin/admin_dashboard.html', context)


@staff_member_required
def admin_activity_log_view(request):
    """
    Display paginated and filterable activity logs.
    """
    logs = AdminActivityLog.objects.select_related('admin').all()
    
    # Filters
    action_filter = request.GET.get('action')
    module_filter = request.GET.get('module')
    admin_filter = request.GET.get('admin')
    search = request.GET.get('search')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    if module_filter:
        logs = logs.filter(module=module_filter)
    if admin_filter:
        logs = logs.filter(admin__id=admin_filter)
    if search:
        logs = logs.filter(
            Q(description__icontains=search) | 
            Q(admin__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all admins for filter dropdown
    admins = CustomUser.objects.filter(is_staff=True)
    
    context = {
        'page_obj': page_obj,
        'admins': admins,
        'action_choices': AdminActivityLog.ACTION_CHOICES,
        'module_choices': AdminActivityLog.MODULE_CHOICES,
    }
    
    return render(request, 'admin/admin_activity_log.html', context)


@user_passes_test(superuser_required)
def terminate_session(request, session_id):
    """
    Terminate an admin session manually.
    """
    if request.method == 'POST':
        try:
            session = AdminSession.objects.get(id=session_id)
            session.is_active = False
            session.logout_time = timezone.now()
            session.save()
            
            # Log the action
            AdminActivityLog.objects.create(
                admin=request.user,
                action='UPDATE',
                module='SESSION',
                description=f'Manually terminated session for {session.user.username}',
                ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0')
            )
            
            return JsonResponse({'success': True, 'message': 'Session terminated successfully'})
        except AdminSession.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Session not found'}, status=404)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)
