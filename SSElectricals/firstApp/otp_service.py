from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import PhoneOTP
from twilio.rest import Client
import random


class OTPService:
    """Service class for handling OTP operations"""
    
    @staticmethod
    def send_otp(phone_number):
        """
        Generate and send OTP to phone number.
        Returns: (success: bool, message: str, otp: str or None)
        """
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_otps = PhoneOTP.objects.filter(
            phone_number=phone_number,
            created_at__gte=one_hour_ago
        ).count()
        
        if recent_otps >= 3:
            return False, "Too many OTP requests. Please try again later.", None
        
        # Invalidate previous OTPs
        PhoneOTP.objects.filter(
            phone_number=phone_number,
            is_verified=False
        ).update(is_verified=True)
        
        # Generate new OTP
        otp_code = PhoneOTP.generate_otp()
        
        # Save to DB
        PhoneOTP.objects.create(
            phone_number=phone_number,
            otp=otp_code
        )
        
        # Send SMS (Twilio)
        success, msg = OTPService._send_sms(phone_number, otp_code)
        if not success:
            return False, msg, None
        
        return True, "OTP sent successfully", otp_code
    
    
    @staticmethod
    def verify_otp(phone_number, otp_code):
        """
        Verify OTP for a phone number.
        """
        try:
            phone_otp = PhoneOTP.objects.filter(
                phone_number=phone_number,
                is_verified=False
            ).order_by('-created_at').first()
            
            if not phone_otp:
                return False, "No OTP found. Please request a new OTP."
            
            success, message = phone_otp.verify(otp_code)
            return success, message
        
        except Exception as e:
            return False, f"Error verifying OTP: {str(e)}"
    
    
    @staticmethod
    def resend_otp(phone_number):
        """
        Resend OTP with cooldown.
        """
        one_minute_ago = timezone.now() - timedelta(seconds=60)
        recent_otp = PhoneOTP.objects.filter(
            phone_number=phone_number,
            created_at__gte=one_minute_ago
        ).first()
        
        if recent_otp:
            return False, "Please wait 60 seconds before requesting a new OTP.", None
        
        return OTPService.send_otp(phone_number)
    
    
    @staticmethod
    def _send_sms(phone_number, otp):
        """
        Send SMS with Twilio.
        Reads credentials from Django settings.
        """
        try:
            client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
            
            message = client.messages.create(
                body=f"Your SSElectricals OTP is: {otp}. Valid for 5 minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,   # Must be a valid Twilio sender
                to=f"+91{phone_number}"               # India format
            )
            
            return True, "SMS sent"
        
        except Exception as e:
            return False, f"SMS sending failed: {str(e)}"
