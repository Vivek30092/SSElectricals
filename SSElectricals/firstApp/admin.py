from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Category, Product, Cart, CartItem, Order, OrderItem, AdminSession, AdminActivityLog, PhoneOTP

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'address', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'address', 'profile_picture')}),
    )

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]

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

class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'otp', 'created_at', 'is_verified', 'retry_count')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('phone_number',)
    readonly_fields = ('otp', 'created_at', 'retry_count')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(AdminSession, AdminSessionAdmin)
admin.site.register(AdminActivityLog, AdminActivityLogAdmin)
admin.site.register(PhoneOTP, PhoneOTPAdmin)
