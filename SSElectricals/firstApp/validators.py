import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_indian_phone(value):
    """
    Validates that the number is a valid Indian mobile number.
    Format: +91-9876543210 or 9876543210
    """
    pattern = re.compile(r"^(\+91[\-\s]?)?[6-9]\d{9}$")
    if not pattern.match(str(value)):
        raise ValidationError(
            _('%(value)s is not a valid Indian phone number'),
            params={'value': value},
        )

def validate_strong_password(value):
    """
    Validates that the password meets strong security criteria:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(value) < 8:
        raise ValidationError(_('Password must be at least 8 characters long.'))
    if not any(char.isupper() for char in value):
        raise ValidationError(_('Password must contain at least one uppercase letter.'))
    if not any(char.islower() for char in value):
        raise ValidationError(_('Password must contain at least one lowercase letter.'))
    if not any(char.isdigit() for char in value):
        raise ValidationError(_('Password must contain at least one number.'))
    if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for char in value):
        raise ValidationError(_('Password must contain at least one special character.'))

def validate_upi_id(value):
    """
    Validates a UPI ID format (e.g., username@bankname).
    """
    pattern = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")
    if not pattern.match(value):
        raise ValidationError(
            _('%(value)s is not a valid UPI ID'),
            params={'value': value},
        )

def validate_address_format(value):
    """
    Basic validation for address format.
    Ensures the address is not just whitespace and has a minimum length.
    """
    if not value or len(value.strip()) < 10:
        raise ValidationError(_('Address must be at least 10 characters long and provide sufficient detail.'))
