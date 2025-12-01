from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # OTP Authentication (Primary for users)
    path('otp-login/', views.otp_login, name='otp_login'),
    path('otp-verify/', views.otp_verify, name='otp_verify'),
    path('signup-otp/', views.signup_otp, name='signup_otp'),
    path('signup-complete/', views.signup_complete, name='signup_complete'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # Password Authentication (For admins)
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='firstApp/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Admin Dashboard URLs
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/activity-log/', admin_views.admin_activity_log_view, name='admin_activity_log'),
    path('admin/terminate-session/<int:session_id>/', admin_views.terminate_session, name='terminate_session'),
    
    # AJAX API endpoints
    path('api/cart/add/', views.ajax_add_to_cart, name='ajax_add_to_cart'),
    path('api/cart/update/', views.ajax_update_cart, name='ajax_update_cart'),
    path('api/search/', views.ajax_search, name='ajax_search'),
]
