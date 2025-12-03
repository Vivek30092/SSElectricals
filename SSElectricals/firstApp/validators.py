from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
import re


def validate_indian_phone(value):
    """Validate 10-digit Indian phone number."""
    if not re.match(r'^[6-9]\d{9}$', value):
        raise ValidationError('Phone number must be 10 digits and start with 6, 7, 8, or 9.')
    return value


def validate_strong_password(value):
    """
    Validate password strength:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 number
    - At least 1 special symbol
    """
    if len(value) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    
    if not re.search(r'[A-Z]', value):
        raise ValidationError('Password must contain at least one uppercase letter.')
    
    if not re.search(r'\d', value):
        raise ValidationError('Password must contain at least one number.')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError('Password must contain at least one special symbol.')
    
    return value


def validate_upi_id(value):
    """Validate UPI ID format (xxxx@upi)."""
    if not re.match(r'^[\w.-]+@[\w.-]+$', value):
        raise ValidationError('Invalid UPI ID format. Example: username@upi')
    return value


def validate_address_format(value):
    """Validate address has minimum required content."""
    if len(value.strip()) < 10:
        raise ValidationError('Address must be at least 10 characters long.')
    return value
