from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import admin_views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/add-review/', views.add_review, name='add_review'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    

    
    # Email OTP Authentication
    path('signup-email/', views.email_signup, name='email_signup'),
    path('signup-email/verify/', views.email_signup_verify, name='email_signup_verify'),
    path('login-email/', views.email_login, name='email_login'),
    path('login-email/verify/', views.email_login_verify, name='email_login_verify'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password/verify/', views.forgot_password_verify, name='forgot_password_verify'),
    path('reset-password/', views.reset_password, name='reset_password'),
    

    
    # Password Authentication (For admins)
    path('signup/', views.signup, name='signup'),
    path('signup/', views.signup, name='signup'),
    # path('login/', auth_views.LoginView.as_view(template_name='firstApp/login.html'), name='login'), # Removed as per request
    path('logout/', auth_views.LogoutView.as_view(next_page='email_login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/change-password/', views.initiate_profile_password_change, name='initiate_profile_password_change'),
    path('profile/change-password/verify/', views.verify_profile_password_change_otp, name='verify_profile_password_change_otp'),
    path('profile/change-password/confirm/', views.change_profile_password, name='change_profile_password'),
    
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Admin Dashboard URLs (Renamed to shop-admin to avoid conflict)
    path('shop-admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('shop-admin/activity-log/', admin_views.admin_activity_log_view, name='admin_activity_log'),
    path('shop-admin/terminate-session/<int:session_id>/', admin_views.terminate_session, name='terminate_session'),
    path('shop-admin/analytics/', admin_views.admin_analytics_new, name='admin_analytics'),
    path('shop-admin/analytics/delete/', admin_views.admin_delete_analytics_file, name='admin_delete_analytics_file'),
    
    # Admin Product Management
    path('shop-admin/products/', admin_views.admin_product_list, name='admin_product_list'),
    path('shop-admin/products/add/', admin_views.admin_product_add, name='admin_product_add'),
    path('shop-admin/products/edit/<int:pk>/', admin_views.admin_product_edit, name='admin_product_edit'),
    path('shop-admin/products/delete/<int:pk>/', admin_views.admin_product_delete, name='admin_product_delete'),
    
    # Admin Category Management
    path('shop-admin/categories/', admin_views.admin_category_list, name='admin_category_list'),
    path('shop-admin/categories/add/', admin_views.admin_category_add, name='admin_category_add'),
    path('shop-admin/categories/edit/<int:pk>/', admin_views.admin_category_edit, name='admin_category_edit'),
    path('shop-admin/categories/delete/<int:pk>/', admin_views.admin_category_delete, name='admin_category_delete'),
    
    # Admin Order Management
    path('shop-admin/orders/', admin_views.admin_order_list, name='admin_order_list'),
    path('shop-admin/orders/<int:pk>/', admin_views.admin_order_detail, name='admin_order_detail'),

    # Admin Reviews
    path('shop-admin/reviews/', admin_views.admin_reviews_list, name='admin_reviews_list'),
    path('shop-admin/reviews/delete/<int:review_id>/', admin_views.admin_delete_review, name='admin_delete_review'),
    path('shop-admin/reviews/approve/<int:review_id>/', admin_views.admin_approve_review, name='admin_approve_review'),

    # Admin Daily Sales
    path('shop-admin/sales/', admin_views.admin_daily_sales, name='admin_daily_sales'),
    path('shop-admin/sales/add/', admin_views.admin_add_daily_sales, name='admin_add_daily_sales'),
    path('shop-admin/sales/edit/<int:pk>/', admin_views.admin_edit_daily_sales, name='admin_edit_daily_sales'),
    path('shop-admin/sales/delete/<int:pk>/', admin_views.admin_delete_daily_sales, name='admin_delete_daily_sales'),
    path('shop-admin/sales/export/', admin_views.admin_export_sales, name='admin_export_sales'),
    path('shop-admin/sales/upload/', admin_views.admin_upload_sales, name='admin_upload_sales'),

    # Admin Daily Expenses
    path('shop-admin/expenses/', admin_views.admin_daily_expenses, name='admin_daily_expenses'),
    path('shop-admin/expenses/add/', admin_views.admin_add_daily_expense, name='admin_add_daily_expense'),
    path('shop-admin/expenses/edit/<int:pk>/', admin_views.admin_edit_daily_expense, name='admin_edit_daily_expense'),
    path('shop-admin/expenses/delete/<int:pk>/', admin_views.admin_delete_daily_expense, name='admin_delete_daily_expense'),
    path('shop-admin/expenses/export/', admin_views.admin_export_expenses, name='admin_export_expenses'),
    path('shop-admin/expenses/upload/', admin_views.admin_upload_expenses, name='admin_upload_expenses'),
    
    # Appointment URLs
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('appointment-success/', views.appointment_success, name='appointment_success'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
    path('cancel-appointment/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    
    # Admin Appointment URLs
    path('shop-admin/appointments/', admin_views.admin_appointment_list, name='admin_appointment_list'),
    path('shop-admin/appointments/update/<int:pk>/', admin_views.admin_appointment_update, name='admin_appointment_update'),
    path('shop-admin/appointments/delete/<int:pk>/', admin_views.admin_appointment_delete, name='admin_appointment_delete'),

    # Admin Analytics URLs
    path('shop-admin/analytics/', admin_views.admin_analytics_new, name='admin_analytics'),

    # Admin User Management
    path('shop-admin/users/', admin_views.admin_user_list, name='admin_user_list'),
    path('shop-admin/users/<int:user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),

    path('confirm-delivery/', views.confirm_delivery_otp, name='confirm_delivery_otp'),
    path('order/receipt/<int:order_id>/', views.order_receipt, name='order_receipt'),
    
    # AJAX API endpoints
    path('api/cart/add/', views.ajax_add_to_cart, name='ajax_add_to_cart'),
    path('api/cart/update/', views.ajax_update_cart, name='ajax_update_cart'),
    path('api/search/', views.ajax_search, name='ajax_search'),
    
    path('reviews/', views.google_reviews, name='google_reviews'),
]
