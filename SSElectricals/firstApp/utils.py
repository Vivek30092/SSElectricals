from django.core.mail import send_mail
from django.conf import settings
import random

def send_otp_email(email, otp):
    """Send OTP to the user's email."""
    subject = 'Your OTP for SSElectricals'
    message = f'Your OTP is {otp}. It is valid for 5 minutes.'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    try:
        send_mail(subject, message, email_from, recipient_list)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
