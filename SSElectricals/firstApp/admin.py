from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import (
    CustomUser, Category, Product, ProductImage, Cart, CartItem, Order, OrderItem,
    AdminSession, AdminActivityLog, Appointment, DailySales, DailyExpenditure, 
    PurchaseEntry, EmailLog, FinancialValidationLog
)
from .utils import save_csv_entry


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'address', 'profile_picture')}),
        ('Order Statistics', {'fields': ('total_orders_count', 'free_delivery_used_count')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'address', 'profile_picture')}),
    )
    readonly_fields = ('total_orders_count', 'free_delivery_used_count')

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_trending')
    search_fields = ('name', 'category__name')
    list_filter = ('category', 'is_trending')
    list_editable = ('is_trending',)
    inlines = [ProductImageInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'delivery_charge', 'status', 'final_price', 'delivery_otp', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__phone_number', 'user__email', 'id')
    readonly_fields = ('created_at',)
    inlines = [OrderItemInline]
    actions = ['generate_delivery_otp', 'approve_free_delivery']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'created_at')
        }),
        ('Pricing', {
            'fields': ('total_price', 'delivery_charge', 'final_price')
        }),
        ('Delivery Details', {
            'fields': ('address', 'distance_km', 'delivery_otp', 'latitude', 'longitude')
        }),
    )

    @admin.action(description='Generate Delivery OTP')
    def generate_delivery_otp(self, request, queryset):
        import random
        count = 0
        for order in queryset:
            if order.status in ['Confirmed', 'Out for Delivery']:
                otp = str(random.randint(100000, 999999))
                order.delivery_otp = otp
                order.save()
                count += 1
        
        self.message_user(request, f"Generated OTP for {count} orders.")

    @admin.action(description='Approve Free Delivery (Set Delivery Charge to 0)')
    def approve_free_delivery(self, request, queryset):
        for order in queryset:
            order.delivery_charge = 0
            order.final_price = order.total_price  # Updates final price to match total only
            order.save()
            # Also increment user's free delivery usage if not already counted? 
            # Logic for that is better handled in save() or signal, but doing it simplistically here:
            user = order.user
            user.free_delivery_used_count += 1
            user.save()
        self.message_user(request, f"Free delivery approved for {queryset.count()} orders.")

class AdminSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_time', 'is_active', 'last_activity')
    list_filter = ('is_active', 'login_time')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('session_key', 'login_time', 'logout_time', 'last_activity')

class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'module', 'timestamp', 'ip_address')
    list_filter = ('action', 'module', 'timestamp')
    search_fields = ('admin__username', 'description')
    readonly_fields = ('admin', 'action', 'module', 'description', 'timestamp', 'ip_address')
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of logs
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete logs



admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(AdminSession, AdminSessionAdmin)
admin.site.register(AdminActivityLog, AdminActivityLogAdmin)

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'service_type', 'date', 'time', 'status', 'total_charge')
    list_filter = ('status', 'service_type', 'date')
    search_fields = ('customer_name', 'phone', 'email')
    readonly_fields = ('created_at',)

class DailySalesAdmin(admin.ModelAdmin):
    list_display = ('date', 'day', 'total_sales', 'remark', 'admin')
    list_filter = ('date', 'remark')
    search_fields = ('remark',)
    
    def save_model(self, request, obj, form, change):
        if not obj.admin:
            obj.admin = request.user
        super().save_model(request, obj, form, change)

class DailyExpenditureAdmin(admin.ModelAdmin):
    list_display = ('date', 'online_amount', 'cash_amount', 'total', 'description', 'admin')
    list_filter = ('date',)
    search_fields = ('description',)

    def save_model(self, request, obj, form, change):
        if not obj.admin:
            obj.admin = request.user
        super().save_model(request, obj, form, change)

class FinancialValidationLogAdmin(admin.ModelAdmin):
    """Admin interface for Financial Validation Logs - Read-only for audit purposes"""
    list_display = ('violation_type', 'detected_at', 'source_module', 'order', 'user')
    list_filter = ('violation_type', 'detected_at')
    search_fields = ('description', 'source_module')
    readonly_fields = ('violation_type', 'description', 'source_module', 'order', 'detected_at', 'ip_address', 'user')
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation - only created by system
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit logs

admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(DailySales, DailySalesAdmin)
admin.site.register(DailyExpenditure, DailyExpenditureAdmin)
admin.site.register(PurchaseEntry)
admin.site.register(FinancialValidationLog, FinancialValidationLogAdmin)



# Signal Handlers for Session Tracking and Activity Logging

def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


@receiver(user_logged_in)
def log_admin_login(sender, request, user, **kwargs):
    """Track admin login sessions."""
    if user.is_staff:
        # Create session record
        session_key = request.session.session_key
        if session_key:
            AdminSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:250],
                is_active=True
            )
        
        # Log the login activity
        AdminActivityLog.objects.create(
            admin=user,
            action='LOGIN',
            module='SESSION',
            description=f'Admin logged in from {get_client_ip(request)}',
            ip_address=get_client_ip(request)
        )


@receiver(user_logged_out)
def log_admin_logout(sender, request, user, **kwargs):
    """Log admin logout."""
    if user and user.is_staff:
        # Mark session as inactive
        session_key = request.session.session_key
        if session_key:
            from django.utils import timezone
            AdminSession.objects.filter(
                session_key=session_key,
                is_active=True
            ).update(
                is_active=False,
                logout_time=timezone.now()
            )
        
        # Log the logout activity
        AdminActivityLog.objects.create(
            admin=user,
            action='LOGOUT',
            module='SESSION',
            description=f'Admin logged out',
            ip_address=get_client_ip(request)
        )


# Track Product CRUD Operations
@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    """Log product creation and updates."""
    from django.contrib.auth import get_user_model
    # Get current user from thread local storage (will be set by middleware)
    user = getattr(instance, '_current_user', None)
    
    if user and user.is_staff:
        action = 'CREATE' if created else 'UPDATE'
        description = f"{'Created' if created else 'Updated'} product: {instance.name} (ID: {instance.id})"
        
        AdminActivityLog.objects.create(
            admin=user,
            action=action,
            module='PRODUCT',
            description=description,
            ip_address=getattr(instance, '_ip_address', '0.0.0.0')
        )


@receiver(post_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    """Log product deletion."""
    user = getattr(instance, '_current_user', None)
    
    if user and user.is_staff:
        AdminActivityLog.objects.create(
            admin=user,
            action='DELETE',
            module='PRODUCT',
            description=f'Deleted product: {instance.name} (ID: {instance.id})',
            ip_address=getattr(instance, '_ip_address', '0.0.0.0')
        )


# Track Category CRUD Operations
@receiver(post_save, sender=Category)
def log_category_save(sender, instance, created, **kwargs):
    """Log category creation and updates."""
    user = getattr(instance, '_current_user', None)
    
    if user and user.is_staff:
        action = 'CREATE' if created else 'UPDATE'
        description = f"{'Created' if created else 'Updated'} category: {instance.name} (ID: {instance.id})"
        
        AdminActivityLog.objects.create(
            admin=user,
            action=action,
            module='CATEGORY',
            description=description,
            ip_address=getattr(instance, '_ip_address', '0.0.0.0')
        )


@receiver(post_delete, sender=Category)
def log_category_delete(sender, instance, **kwargs):
    """Log category deletion."""
    user = getattr(instance, '_current_user', None)
    
    if user and user.is_staff:
        AdminActivityLog.objects.create(
            admin=user,
            action='DELETE',
            module='CATEGORY',
            description=f'Deleted category: {instance.name} (ID: {instance.id})',
            ip_address=getattr(instance, '_ip_address', '0.0.0.0')
        )


# Track Order Updates (status changes)
_order_original_status = {}

@receiver(pre_save, sender=Order)
def track_order_status(sender, instance, **kwargs):
    """Track original order status before save."""
    if instance.pk:
        try:
            original = Order.objects.get(pk=instance.pk)
            _order_original_status[instance.pk] = original.status
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def log_order_save(sender, instance, created, **kwargs):
    """Log order status changes and SEND EMAIL."""
    user = getattr(instance, '_current_user', None)
    
    # Activity Log
    if user and user.is_staff:
        if created:
            description = f'Created order #{instance.id} for user {instance.user.username}'
            action = 'CREATE'
        else:
            # Check if status changed
            old_status = _order_original_status.get(instance.pk)
            if old_status and old_status != instance.status:
                description = f'Updated order #{instance.id} status from {old_status} to {instance.status}'
                action = 'UPDATE'
            else:
                description = f'Updated order #{instance.id}'
                action = 'UPDATE'
            
            # Clean up tracking dict
            if instance.pk in _order_original_status:
                del _order_original_status[instance.pk]
        
        AdminActivityLog.objects.create(
            admin=user,
            action=action,
            module='ORDER',
            description=description,
            ip_address=getattr(instance, '_ip_address', '0.0.0.0')
        )

    # --- EMAIL NOTIFICATION LOGIC ---
    # NOTE: Email notifications are now handled ONLY in admin_views.py using email_utils module
    # This prevents duplicate emails from being sent to users.
    # The email_utils module provides professional HTML templates with logging and retry logic.


# Unified CSV Storage Signals
@receiver(post_save, sender=DailySales)
def log_daily_sales_csv(sender, instance, created, **kwargs):
    if created:
        data = {
            'Date': str(instance.date),
            'Day': instance.day or '',
            'Daily sales amount': str(instance.total_sales),
            'Total online money received': str(instance.online_received),
            'Total cash received': str(instance.cash_received),
            'Labor Charge': str(instance.labor_charge) if instance.labor_charge is not None else '0.00',
            'Delivery Charge': str(instance.delivery_charge) if instance.delivery_charge is not None else '0.00',
            'Subtotal': str(instance.subtotal),
            'Remark': instance.remark,
            'Admin ID': instance.admin.username if instance.admin else 'Unknown'
        }
        headers = ['Date', 'Day', 'Daily sales amount', 'Total online money received', 'Total cash received', 'Labor Charge', 'Delivery Charge', 'Subtotal', 'Remark', 'Admin ID']
        save_csv_entry('daily_sales.csv', data, headers)


@receiver(post_save, sender=DailyExpenditure)
def log_expenses_csv(sender, instance, created, **kwargs):
    if created:
        data = {
            'Date': str(instance.date),
            'Online Amount': str(instance.online_amount) if instance.online_amount is not None else '0.00',
            'Cash Amount': str(instance.cash_amount) if instance.cash_amount is not None else '0.00',
            'Total': str(instance.total),
            'Added by': instance.admin.username if instance.admin else 'Unknown',
            'Description': instance.description
        }
        headers = ['Date', 'Online Amount', 'Cash Amount', 'Total', 'Added by', 'Description']
        save_csv_entry('expenses.csv', data, headers)

