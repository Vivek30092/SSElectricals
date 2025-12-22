"""
Professional Email Utilities for SSElectricals
Handles all email sending with logging, retry logic, and HTML templates
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import EmailLog, Order, Appointment
import logging
from typing import Optional, Dict, Any
from threading import Thread

logger = logging.getLogger(__name__)

# Business Information
BUSINESS_INFO = {
    'name': 'Shiv Shakti Electricals',
    'address': 'Indore, Madhya Pradesh, India',
    'phone': '+91-9993149226',
    'email': 'shivshaktielectrical1430@gmail.com',
    'website': 'https://yourdomain.com',  # Update with actual domain
}


def send_professional_email(
    email_type: str,
    recipient: str,
    subject: str,
    template_name: str,
    context: Dict[str, Any],
    order: Optional[Order] = None,
    appointment: Optional[Appointment] = None,
    attachments: list = None,
    high_priority: bool = False
) -> bool:
    """
    Send professional HTML email with logging and error handling
    
    Args:
        email_type: Type of email from EmailLog.EMAIL_TYPE_CHOICES
        recipient: Email address
        subject: Email subject line
        template_name: Path to HTML template (relative to templates/emails/)
        context: Template context dictionary
        order: Related order object (optional)
        appointment: Related appointment object (optional)
        attachments: List of (filename, content, mimetype) tuples
        high_priority: Whether to set X-Priority header
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    # Create email log entry
    email_log = EmailLog.objects.create(
        email_type=email_type,
        recipient=recipient,
        subject=subject,
        status='PENDING',
        order=order,
        appointment=appointment
    )
    
    try:
        # Add business info to context
        context['business'] = BUSINESS_INFO
        context['current_year'] = timezone.now().year
        
        # Render HTML content
        html_content = render_to_string(f'emails/{template_name}', context)
        
        # Create plain text version (strip HTML tags)
        from django.utils.html import strip_tags
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Add attachments if any
        if attachments:
            for filename, content, mimetype in attachments:
                email.attach(filename, content, mimetype)
        
        # Set priority if high priority
        if high_priority:
            email.extra_headers = {'X-Priority': '1'}
        
        # Send email
        email.send(fail_silently=False)
        
        # Update log as sent
        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()
        
        logger.info(f"Email sent successfully: {email_type} to {recipient}")
        return True
        
    except Exception as e:
        # Log the error
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.retry_count += 1
        email_log.save()
        
        logger.error(f"Failed to send email: {email_type} to {recipient}. Error: {str(e)}")
        return False


def send_email_async(email_type, recipient, subject, template_name, context, **kwargs):
    """
    Send email asynchronously in a separate thread
    Use this for non-critical emails to avoid blocking
    """
    thread = Thread(
        target=send_professional_email,
        args=(email_type, recipient, subject, template_name, context),
        kwargs=kwargs
    )
    thread.daemon = True
    thread.start()


# ===================================================================
# Specific Email Functions
# ===================================================================

def send_order_status_email(order: Order):
    """Send email when order status changes"""
    context = {
        'order': order,
        'user': order.user,
        'items': order.items.all(),
        'status': order.get_status_display(),
    }
    
    subject = f"Order Status Update - {order.get_status_display()}"
    
    send_email_async(
        email_type='ORDER_STATUS',
        recipient=order.user.email,
        subject=subject,
        template_name='order_status_update.html',
        context=context,
        order=order
    )


def send_delivery_otp_email(order: Order, otp: str):
    """Send delivery OTP when order is out for delivery"""
    context = {
        'order': order,
        'user': order.user,
        'otp': otp,
        'items': order.items.all(),
    }
    
    subject = f"Your Delivery OTP - Order #{order.id}"
    
    return send_professional_email(
        email_type='DELIVERY_OTP',
        recipient=order.user.email,
        subject=subject,
        template_name='delivery_otp.html',
        context=context,
        order=order,
        high_priority=True  # OTP emails are high priority
    )


SITE_URL = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')

def send_order_delivered_email(order: Order):
    """Send email when order is delivered with review request"""
    context = {
        'order': order,
        'user': order.user,
        'items': order.items.all(),
        'site_url': SITE_URL,
        'review_url': f"{SITE_URL}/orders/", 
    }
    
    subject = "Order Delivered Successfully - We'd Love Your Feedback"
    
    send_email_async(
        email_type='ORDER_DELIVERED',
        recipient=order.user.email,
        subject=subject,
        template_name='order_delivered.html',
        context=context,
        order=order
    )


def send_appointment_status_email(appointment: Appointment):
    """Send email when appointment status changes"""
    context = {
        'appointment': appointment,
        'customer_name': appointment.customer_name,
        'status': appointment.get_status_display(),
    }
    
    subject = f"Service Appointment Update - {appointment.get_status_display()}"
    
    send_email_async(
        email_type='APPOINTMENT_STATUS',
        recipient=appointment.email,
        subject=subject,
        template_name='appointment_status.html',
        context=context,
        appointment=appointment
    )


def send_appointment_complete_email(appointment: Appointment):
    """Send email when appointment is completed with review request"""
    context = {
        'appointment': appointment,
        'customer_name': appointment.customer_name,
        'review_url': f"{settings.SITE_URL}/appointments/{appointment.id}/review/",  # Update with actual URL
    }
    
    subject = "Service Completed - Share Your Experience"
    
    send_email_async(
        email_type='APPOINTMENT_COMPLETE',
        recipient=appointment.email,
        subject=subject,
        template_name='appointment_complete.html',
        context=context,
        appointment=appointment
    )


def retry_failed_emails(max_retries=3):
    """
    Retry failed emails (to be called from a scheduled task)
    """
    failed_emails = EmailLog.objects.filter(
        status='FAILED',
        retry_count__lt=max_retries
    ).order_by('created_at')[:50]  # Process 50 at a time
    
    for email_log in failed_emails:
        # Mark as retry
        email_log.status = 'RETRY'
        email_log.save()
        
        # Attempt to resend based on type
        # This would require reconstructing context from order/appointment
        # Implement based on your retry strategy
        logger.info(f"Retrying email: {email_log.id}")


# ===================================================================
# NEW: Professional Email Functions (December 2024)
# ===================================================================

def send_appointment_confirmed_email(appointment, electrician=None):
    """
    Send appointment confirmation email to user
    Trigger: Appointment booked (by user or admin) and confirmed
    """
    from .models import Electrician
    
    context = {
        'user_name': appointment.customer_name,
        'service_name': appointment.service.name if appointment.service else 'General Service',
        'appointment_date': appointment.date.strftime('%A, %d %B %Y'),
        'appointment_time': appointment.time.strftime('%I:%M %p'),
        'base_charge': float(appointment.visiting_charge),
        'user_phone': appointment.phone,
        'user_address': f"{appointment.house_number}, {appointment.address_line1}, {appointment.address_line2 or ''}, {appointment.area}, {appointment.city} - {appointment.pincode}",
        'business_profile_link': 'https://g.page/r/YOUR_GOOGLE_PROFILE',  # Update with actual link
    }
    
    if electrician:
        context['electrician_name'] = electrician.name
        context['electrician_phone'] = electrician.phone_number
    
    subject = f"✅ Appointment Confirmed - {context['service_name']} on {context['appointment_date']}"
    
    send_email_async(
        email_type='APPOINTMENT_STATUS',
        recipient=appointment.email,
        subject=subject,
        template_name='appointment_confirmed.html',
        context=context,
        appointment=appointment
    )


def send_electrician_assignment_email(appointment, electrician):
    """
    Send assignment notification to electrician
    Trigger: Admin assigns an electrician to an appointment
    """
    context = {
        'electrician_name': electrician.name,
        'service_name': appointment.service.name if appointment.service else 'General Service',
        'appointment_date': appointment.date.strftime('%A, %d %B %Y'),
        'appointment_time': appointment.time.strftime('%I:%M %p'),
        'customer_name': appointment.customer_name,
        'customer_phone': appointment.phone,
        'customer_address': f"{appointment.house_number}, {appointment.address_line1}, {appointment.address_line2 or ''}, {appointment.area}, {appointment.city} - {appointment.pincode}",
        'base_charge': float(appointment.visiting_charge),
        'problem_description': appointment.problem_description,
        'admin_contact': BUSINESS_INFO['phone'],
    }
    
    subject = f"🔧 New Appointment Assigned - {context['appointment_date']} at {context['appointment_time']}"
    
    send_email_async(
        email_type='APPOINTMENT_STATUS',
        recipient=electrician.email,
        subject=subject,
        template_name='electrician_assigned.html',
        context=context,
        appointment=appointment
    )


def send_appointment_completed_review_email(appointment, review_link=None):
    """
    Send completion email to user with review request
    Trigger: Appointment status updated to Completed
    """
    context = {
        'user_name': appointment.customer_name,
        'service_name': appointment.service.name if appointment.service else 'General Service',
        'appointment_date': appointment.date.strftime('%d %B %Y'),
        'electrician_name': appointment.assigned_electrician.name if appointment.assigned_electrician else None,
        'review_link': review_link or 'https://g.page/r/YOUR_GOOGLE_PROFILE/review',  # Update with actual link
        'business_profile_link': 'https://g.page/r/YOUR_GOOGLE_PROFILE',  # Update with actual link
    }
    
    subject = f"⭐ Service Completed - Share Your Experience with {BUSINESS_INFO['name']}"
    
    send_email_async(
        email_type='APPOINTMENT_COMPLETE',
        recipient=appointment.email,
        subject=subject,
        template_name='appointment_completed_review.html',
        context=context,
        appointment=appointment
    )


def send_order_status_update_email(order, admin_message=None):
    """
    Send generic order status update email
    Trigger: Whenever admin updates order status
    """
    items = order.items.all()
    product_names = ', '.join([item.product.name for item in items[:3]])
    if items.count() > 3:
        product_names += f' + {items.count() - 3} more'
    
    context = {
        'user_name': order.user.get_full_name() or order.customer_name or order.user.username,
        'order_id': order.id,
        'product_name': product_names,
        'order_status': order.get_status_display(),
        'admin_message': admin_message,
        'dashboard_link': f"{SITE_URL}/orders/",
    }
    
    subject = f"📦 Order #{order.id} - Status: {order.get_status_display()}"
    
    send_email_async(
        email_type='ORDER_STATUS',
        recipient=order.user.email,
        subject=subject,
        template_name='order_status_generic.html',
        context=context,
        order=order
    )


def send_order_out_for_delivery_email(order, otp):
    """
    Send out for delivery email with OTP
    Trigger: Order status changes to Out for Delivery
    """
    items = order.items.all()
    product_names = ', '.join([item.product.name for item in items[:3]])
    if items.count() > 3:
        product_names += f' + {items.count() - 3} more'
    
    context = {
        'user_name': order.user.get_full_name() or order.customer_name or order.user.username,
        'order_id': order.id,
        'product_name': product_names,
        'delivery_otp': otp,
    }
    
    subject = f"🚚 Your Order #{order.id} is Out for Delivery - OTP Inside"
    
    return send_professional_email(
        email_type='DELIVERY_OTP',
        recipient=order.user.email,
        subject=subject,
        template_name='order_out_for_delivery.html',
        context=context,
        order=order,
        high_priority=True  # OTP emails are high priority
    )


def send_order_delivered_review_email(order, product_review_link=None):
    """
    Send order delivered email with product review request
    Trigger: Order status updated to Delivered
    """
    items = order.items.all()
    product_names = ', '.join([item.product.name for item in items[:3]])
    if items.count() > 3:
        product_names += f' + {items.count() - 3} more'
    
    # Get first product for review link
    first_item = items.first()
    
    context = {
        'user_name': order.user.get_full_name() or order.customer_name or order.user.username,
        'order_id': order.id,
        'product_name': product_names,
        'delivery_date': timezone.now().strftime('%d %B %Y'),
        'product_review_link': product_review_link or f"{SITE_URL}/product/{first_item.product.id}/" if first_item else f"{SITE_URL}/products/",
    }
    
    subject = f"✅ Order Delivered - We'd Love Your Feedback!"
    
    send_email_async(
        email_type='ORDER_DELIVERED',
        recipient=order.user.email,
        subject=subject,
        template_name='order_delivered_review.html',
        context=context,
        order=order
    )


def send_warranty_registered_email(warranty, dashboard_link=None):
    """
    Send warranty registration confirmation email
    Trigger: Admin registers a product warranty
    """
    context = {
        'user_name': warranty.customer_name,
        'product_name': warranty.product_name,
        'product_brand': warranty.product_brand,
        'product_serial': warranty.product_serial,
        'purchase_date': warranty.purchase_date.strftime('%d %B %Y'),
        'warranty_expiry_date': warranty.warranty_expiry_date.strftime('%d %B %Y'),
        'dashboard_link': dashboard_link or f"{SITE_URL}/my-warranties/",
    }
    
    subject = f"🛡️ Warranty Registered - {warranty.product_name}"
    
    send_email_async(
        email_type='WARRANTY',
        recipient=warranty.customer_email,
        subject=subject,
        template_name='warranty_registered.html',
        context=context
    )


def send_price_confirmed_email(recipient_email, user_name, product_name, product_price, 
                               delivery_charge, total_amount, confirm_link=None, 
                               quantity=1, discount=0, validity_days=7):
    """
    Send price confirmation email for order enquiry flow
    Trigger: Admin confirms product price after enquiry
    """
    context = {
        'user_name': user_name,
        'product_name': product_name,
        'product_price': product_price,
        'delivery_charge': delivery_charge,
        'total_amount': total_amount,
        'quantity': quantity,
        'discount': discount,
        'confirm_link': confirm_link,
        'dashboard_link': f"{SITE_URL}/orders/",
        'validity_days': validity_days,
    }
    
    subject = f"💰 Price Confirmed for {product_name} - Action Required"
    
    send_email_async(
        email_type='ORDER_STATUS',
        recipient=recipient_email,
        subject=subject,
        template_name='price_confirmed.html',
        context=context
    )

