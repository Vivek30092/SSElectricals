from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import CustomUser, Category, Product, ProductImage, Cart, CartItem, Order, OrderItem, AdminSession, AdminActivityLog, Appointment, DailySales, DailyExpenditure, PurchaseEntry

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'address', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'address', 'profile_picture')}),
    )

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)
    inlines = [ProductImageInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'final_price', 'delivery_otp', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
    actions = ['generate_delivery_otp']

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

admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(DailySales)
admin.site.register(DailyExpenditure)
admin.site.register(PurchaseEntry)


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
    """Log order status changes."""
    user = getattr(instance, '_current_user', None)
    
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
