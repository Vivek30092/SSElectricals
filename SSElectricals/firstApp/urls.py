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
    
    path('my-receipts/', views.user_receipts, name='user_receipts'),
    path('receipt/<int:receipt_id>/view/', views.receipt_print, name='user_receipt_view'),
    
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Test Pages (Development Only)
    path('test-404/', views.test_404, name='test_404'),
    
    # Admin Dashboard URLs (Renamed to shop-admin to avoid conflict)
    path('shop-admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('shop-admin/activity-log/', admin_views.admin_activity_log_view, name='admin_activity_log'),
    path('shop-admin/terminate-session/<int:session_id>/', admin_views.terminate_session, name='terminate_session'),
    path('shop-admin/analytics/', admin_views.admin_analytics_new, name='admin_analytics'),
    path('shop-admin/analytics/delete/', admin_views.admin_delete_analytics_file, name='admin_delete_analytics_file'),
    
     # Receipt Management
    path('shop-admin/receipt/create/', views.create_receipt, name='create_receipt'),
    path('shop-admin/receipt/', views.receipt_list, name='receipt_list'),
    path('shop-admin/receipt/<int:receipt_id>/', views.receipt_detail, name='receipt_detail'),
    path('shop-admin/receipt/<int:receipt_id>/print/', views.receipt_print, name='receipt_print'),
    path('shop-admin/receipt/<int:receipt_id>/void/', views.void_receipt, name='void_receipt'),
    path('shop-admin/receipt/<int:receipt_id>/correct/', views.create_correction, name='create_correction'),
    path('shop-admin/receipt/<int:receipt_id>/pdf/', views.receipt_pdf, name='receipt_pdf'),
    path('api/products/search/', views.search_products_api, name='search_products_api'),
    
    # Order Receipt
    path('shop-admin/orders/<int:order_id>/receipt-print/', views.order_receipt_print, name='order_receipt_print'),
    
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
    path('api/service-price/', views.get_service_price, name='get_service_price'),
    
    # Admin Appointment URLs
    path('shop-admin/appointments/', admin_views.admin_appointment_list, name='admin_appointment_list'),
    path('shop-admin/appointments/update/<int:pk>/', admin_views.admin_appointment_update, name='admin_appointment_update'),
    path('shop-admin/appointments/delete/<int:pk>/', admin_views.admin_appointment_delete, name='admin_appointment_delete'),
    
    # Admin Service Pricing URLs
    path('shop-admin/service-prices/', admin_views.admin_service_prices, name='admin_service_prices'),
    path('shop-admin/service-prices/save/', admin_views.admin_service_price_save, name='admin_service_price_save'),
    path('shop-admin/service-prices/delete/<int:pk>/', admin_views.admin_service_price_delete, name='admin_service_price_delete'),
    path('shop-admin/service-prices/bulk-create/', admin_views.admin_bulk_create_prices, name='admin_bulk_create_prices'),

    # Admin Analytics URLs
    path('shop-admin/analytics/', admin_views.admin_analytics_new, name='admin_analytics'),
    path('shop-admin/api/analytics/', admin_views.analytics_api, name='analytics_api'),

    # Admin User Management
    path('shop-admin/users/', admin_views.admin_user_list, name='admin_user_list'),
    path('shop-admin/users/<int:user_id>/', admin_views.admin_user_detail, name='admin_user_detail'),

    path('confirm-delivery/', views.confirm_delivery_otp, name='confirm_delivery_otp'),
    path('order/receipt/<int:order_id>/', views.order_receipt, name='order_receipt'),
    
    # AJAX API endpoints
    path('api/cart/add/', views.ajax_add_to_cart, name='ajax_add_to_cart'),
    path('api/cart/update/', views.ajax_update_cart, name='ajax_update_cart'),
    path('api/search/', views.ajax_search, name='ajax_search'),
    
    # Google Reviews
    path('reviews/', views.google_reviews, name='google_reviews'),
    path('api/google-reviews/', views.google_reviews_api, name='google_reviews_api'),
    
    path('onetap-login/request/', views.onetap_login_request, name='onetap_login_request'),
    path('onetap-login/verify/<str:token>/', views.onetap_login_verify, name='onetap_login_verify'),
    path('onetap-login/sent/', views.onetap_login_sent, name='onetap_login_sent'),
    
    # Google OAuth Login
    path('google-login/', views.google_login_redirect, name='google_login'),
    
    # TASK 2: Admin Notification Management
    path('shop-admin/notifications/', admin_views.admin_notifications_list, name='admin_notifications_list'),
    path('shop-admin/notifications/create/', admin_views.admin_notification_create, name='admin_notification_create'),
    path('shop-admin/notifications/\u003cint:pk\u003e/', admin_views.admin_notification_detail, name='admin_notification_detail'),
    path('shop-admin/notifications/\u003cint:pk\u003e/edit/', admin_views.admin_notification_edit, name='admin_notification_edit'),
    path('shop-admin/notifications/\u003cint:pk\u003e/delete/', admin_views.admin_notification_delete, name='admin_notification_delete'),
    
    # TASK 2: User Notifications (User side)
    path('notifications/', views.user_notifications, name='user_notifications'),
    path('notifications/\u003cint:pk\u003e/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:pk>/delete/', views.delete_notification, name='delete_notification'),
]
