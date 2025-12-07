from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags

def send_otp_email(email, otp):
    """Send OTP to the user's email with HTML and plain text alternatives."""
    subject = 'Shiv Shakti Electrical – Your OTP Verification Code'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]

    # Plain text content
    text_content = f"""
Hello,

Your OTP for verification is: {otp}

This OTP is valid for 5 minutes.
If you did not request this code, please ignore this email. Do not share this code with anyone.

Regards,
Shiv Shakti Electrical, Indore (M.P.)
"""

    # HTML content
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            color: #ffc107;
        }}
        .otp-box {{
            background-color: #ffffff;
            border: 2px dashed #ffc107;
            padding: 15px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            letter-spacing: 5px;
            margin: 20px 0;
            color: #000;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 12px;
            color: #777;
            text-align: center;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }}
        .warning {{
            color: #d9534f;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Shiv Shakti Electrical</h2>
        </div>
        <p>Hello,</p>
        <p>You requested a verification code for your account. Please use the One-Time Password (OTP) below to proceed:</p>
        
        <div class="otp-box">
            {otp}
        </div>
        
        <p><strong>Note:</strong> This OTP is valid for <strong>5 minutes</strong>.</p>
        
        <p class="warning">Security Warning: If you did not request this code, please ignore this email. Never share your OTP with anyone, including our support team.</p>
        
        <br>
        <p>Regards,<br>
        <strong>Shiv Shakti Electrical</strong><br>
        Indore (M.P.)</p>
        
        <div class="footer">
            &copy; Shiv Shakti Electricals. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

    try:
        msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

import requests
from django.conf import settings

# Approximate location for Shiv Shakti Electrical, Indore (using Indore center if exact lat/lng unknown)
# Or use the Place ID to get it, but hardcoding is faster for now.
# 22.7533° N, 75.8937° E (Example near Vijay Nagar/Sukhliya where many areas are listed)
SHOP_LAT = 22.7533
SHOP_LNG = 75.8937

def calculate_distance_and_price(user_address):
    """
    Calculate distance using Google Maps API and determine delivery price.
    Returns: (distance_km, price, error_message)
    """
    api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    if not api_key:
        # Fallback or dev mode: return mock
        # Assuming user entered a text address strings, we can't easily guess distance without API
        # For dev, we might return a default 5km
        return 5.0, 70.0, None 
        
    origin = f"{SHOP_LAT},{SHOP_LNG}"
    destination = user_address
    
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK':
            element = data['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                distance_text = element['distance']['text']
                distance_value = element['distance']['value'] # in meters
                distance_km = distance_value / 1000.0
                
                # Pricing Logic
                # Within 3 KM -> 50
                # Within 7 KM -> 70
                # > 7 KM -> No delivery
                
                price = 0
                if distance_km <= 3:
                    price = 50
                elif distance_km <= 7:
                    price = 70
                else:
                    return distance_km, 0, "Delivery not available for distances greater than 7 KMs."
                
                return distance_km, price, None
            else:
                return 0, 0, f"Address could not be located: {element['status']}"
        else:
            return 0, 0, f"Distance API Error: {data['status']}"
            
    except Exception as e:
        return 0, 0, f"Error calculating distance: {str(e)}"



