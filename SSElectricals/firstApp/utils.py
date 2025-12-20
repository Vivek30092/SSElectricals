from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags

def mask_email(email):
    """
    Masks the email address for security.
    Example: johndoe@gmail.com -> j*****e@gmail.com
    Rules: Show only 1st char and last char before @.
    """
    if not email or '@' not in email:
        return email
        
    try:
        local_part, domain = email.split('@')
        if len(local_part) <= 2:
            masked_local = local_part # Too short to mask
        else:
            masked_local = local_part[0:3] + '*' * 5 + local_part[-3:]
            
        return f"{masked_local}@{domain}"
    except:
        return email

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def send_otp_email(email, otp):
    """Send OTP to the user's email with HTML and plain text alternatives."""
    subject = 'Shiv Shakti Electrical – Your OTP Verification Code'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    masked_email = mask_email(email)

    # Plain text content
    text_content = f"""
Hello,

Your OTP for verification is: {otp}

This OTP was requested for: {masked_email}

This OTP is valid for 5 minutes.
If you did not request this code, please ignore this email. Do not share this code with anyone.

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

def send_onetap_login_email(email, login_url):
    """Send one-tap login magic link to the user's email."""
    subject = 'Shiv Shakti Electrical – One-Tap Login Link'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    masked_email = mask_email(email)

    # Plain text content
    text_content = f"""
Hello,

You requested a one-tap login link for your account.

Click the link below to log in securely:
{login_url}

This login link was requested for: {masked_email}

This link is valid for 10 minutes.
If you did not request this link, please ignore this email.

For security reasons, this link can only be used once.

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
        .login-button {{
            display: inline-block;
            background-color: #ffc107;
            color: #000;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            font-size: 16px;
            margin: 20px 0;
            text-align: center;
        }}
        .login-button:hover {{
            background-color: #ffca2c;
        }}
        .button-container {{
            text-align: center;
            margin: 30px 0;
        }}
        .info-box {{
            background-color: #ffffff;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
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
        <p>You requested a one-tap login link for your account. Click the button below to securely log in:</p>
        
        <div class="button-container">
            <a href="{login_url}" class="login-button">🔐 Log In Securely</a>
        </div>
        
        <div class="info-box">
            <p><strong>Account:</strong> {masked_email}</p>
            <p><strong>Valid for:</strong> 10 minutes</p>
            <p><strong>One-time use:</strong> This link can only be used once</p>
        </div>
        
        <p class="warning">Security Warning: If you did not request this login link, please ignore this email. Never share this link with anyone, including our support team.</p>
        
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
        print(f"Error sending one-tap login email: {e}")
        return False

def send_order_status_email(order):
    """
    Send email notification to user when order status changes.
    """
    subject = f'Order Notification - {order.status} (Order #{order.id})'
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [order.user.email]
    
    # Determine Status Color
    status_color = "#17a2b8" # Info
    if order.status == 'Confirmed':
        status_color = "#28a745"
    elif order.status == 'Out for Delivery':
        status_color = "#ffc107"
    elif order.status == 'Delivered':
        status_color = "#007bff"
    elif order.status == 'Cancelled':
        status_color = "#dc3545"

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #444; }}
        .container {{ max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 8px; overflow: hidden; }}
        .header {{ background-color: #343a40; color: #fff; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .status-badge {{ background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 4px; display: inline-block; font-weight: bold; }}
        .details {{ margin-top: 20px; border-top: 1px solid #ddd; padding-top: 20px; }}
        .footer {{ background-color: #eee; padding: 15px; text-align: center; font-size: 12px; color: #777; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ border-bottom: 1px solid #eee; padding: 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Shiv Shakti Electrical</h2>
        </div>
        <div class="content">
            <h3>Hello {order.user.username},</h3>
            <p>Your order <strong>#{order.id}</strong> status has been updated.</p>
            
            <p>Current Status: <span class="status-badge">{order.status}</span></p>
            
            <div class="details">
                <h4>Order Details:</h4>
                <p><strong>Total Amount:</strong> ₹{order.grand_total}</p>
                <p><strong>Delivery Charge:</strong> ₹{order.delivery_charge} 
                   <small>({'Confirmed' if order.final_price else 'Estimated'})</small>
                </p>
                
                <h4>Items:</h4>
                <ul>
    """
    
    for item in order.items.all():
        html_content += f"<li>{item.quantity} x {item.product.name} - ₹{item.price}</li>"
        
    html_content += f"""
                </ul>
            </div>
            
            <p><strong>Delivery Address:</strong><br>{order.address}</p>
            
            <br>
            <p>If you have any questions, please contact us at:</p>
            <p>📞 +91 9977228020<br>✉️ shivshaktielectrical1430@gmail.com</p>
        </div>
        <div class="footer">
            &copy; 2025 Shiv Shakti Electrical. All rights reserved.
        </div>
    </div>
</body>
</html>
    """
    
    text_content = strip_tags(html_content)
    
    try:
        msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Error sending order status email: {e}")
        return False

from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from django.conf import settings
import requests

# Approximate location for Shiv Shakti Electrical, Indore
SHOP_LAT = 22.7624113
SHOP_LNG = 75.8692938

def calculate_distance_and_price(user_address):
    """
    Calculate ROAD distance using Google Maps Distance Matrix API.
    This gives actual driving distance, not straight-line distance.
    
    Returns: (distance_km, price, error_message, latitude, longitude)
    """
    # Use server API key for backend calls (no HTTP referer restrictions)
    api_key = getattr(settings, 'GOOGLE_SERVER_API_KEY', None) or getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    
    user_lat = None
    user_lng = None
    distance_km = 0
    
    # Ensure Indore is in the address for accurate results
    search_address = user_address
    if "indore" not in search_address.lower():
        search_address += ", Indore"
    if "india" not in search_address.lower():
        search_address += ", India"
    
    print(f"[Distance Calc] Input: '{user_address}' → Search: '{search_address}'")
    
    # Try Google APIs if key exists
    if api_key:
        try:
            # Step 1: Geocode the address to get coordinates
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(search_address)}&key={api_key}&region=in"
            
            print(f"[Distance Calc] Calling Geocoding API...")
            geocode_response = requests.get(geocode_url, timeout=10)
            geocode_data = geocode_response.json()
            
            print(f"[Distance Calc] Geocoding status: {geocode_data.get('status', 'Unknown')}")
            
            if geocode_data['status'] == 'OK' and geocode_data['results']:
                location = geocode_data['results'][0]['geometry']['location']
                user_lat = location['lat']
                user_lng = location['lng']
                
                print(f"[Distance Calc] Geocoded to: {user_lat}, {user_lng}")
                
                # Validate the result is in Indore area (approximate bounds check)
                if not (22.5 <= user_lat <= 23.0 and 75.5 <= user_lng <= 76.2):
                    print(f"[Distance Calc] WARNING: Location outside Indore bounds!")
                    return 0, 0, "Address appears to be outside Indore service area. Please verify.", user_lat, user_lng
                
                # Step 2: Use Distance Matrix API for ROAD distance
                origin = f"{SHOP_LAT},{SHOP_LNG}"
                destination = f"{user_lat},{user_lng}"
                
                distance_url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&mode=driving&key={api_key}"
                
                print(f"[Distance Calc] Calling Distance Matrix API...")
                distance_response = requests.get(distance_url, timeout=10)
                distance_data = distance_response.json()
                
                print(f"[Distance Calc] Distance Matrix status: {distance_data.get('status', 'Unknown')}")
                
                if distance_data['status'] == 'OK':
                    if distance_data['rows'] and distance_data['rows'][0]['elements']:
                        element = distance_data['rows'][0]['elements'][0]
                        
                        print(f"[Distance Calc] Element status: {element.get('status', 'Unknown')}")
                        
                        if element['status'] == 'OK':
                            # Road distance in meters -> km
                            distance_value = element['distance']['value']
                            distance_km = round(distance_value / 1000.0, 2)  # Round to 2 decimals
                            
                            # Duration info
                            duration_text = element.get('duration', {}).get('text', 'N/A')
                            print(f"✓ [Distance Calc] ROAD Distance: {distance_km} KM, ETA: {duration_text}")
                            
                            return _calculate_price(distance_km, user_lat, user_lng)
                        else:
                            print(f"[Distance Calc] Element Error: {element['status']}")
                            # Fall through to geodesic calculation
                else:
                    print(f"[Distance Calc] Distance Matrix API Error: {distance_data}")
                    # Fall through to geodesic calculation
            else:
                error_msg = geocode_data.get('error_message', geocode_data.get('status', 'No results'))
                print(f"[Distance Calc] Geocoding failed: {error_msg}")
                # Fall through to Geopy fallback
                
        except requests.exceptions.Timeout:
            print("[Distance Calc] Google API Timeout!")
        except Exception as e:
            print(f"[Distance Calc] Google API Exception: {e}")
            # Fall through to Geopy fallback
    else:
        print("[Distance Calc] No API key found, using Geopy fallback")
    
    # Fallback 1: If we have coordinates but Distance Matrix failed, use geodesic
    if user_lat and user_lng:
        from geopy.distance import geodesic
        user_coords = (user_lat, user_lng)
        shop_coords = (SHOP_LAT, SHOP_LNG)
        distance_km = round(geodesic(shop_coords, user_coords).km, 2)  # Round to 2 decimals
        print(f"⚠ [Distance Calc] Using GEODESIC (straight-line): {distance_km} KM")
        return _calculate_price(distance_km, user_lat, user_lng)
    
    # Fallback 2: Geopy (Nominatim) for geocoding + geodesic distance
    try:
        from geopy.geocoders import Nominatim
        from geopy.distance import geodesic
        
        print("[Distance Calc] Using Geopy fallback for geocoding...")
        geolocator = Nominatim(user_agent="sselectricals_app_v2", timeout=10)
        
        # Add location context
        search_query = search_address
        if "madhya pradesh" not in search_query.lower():
            search_query += ", Madhya Pradesh"
        
        # Viewbox around Indore for bounded search
        viewbox = [
            (23.0, 75.5),  # North-West
            (22.5, 76.2)   # South-East
        ]
        
        location = geolocator.geocode(search_query, viewbox=viewbox, bounded=True)
        
        if location:
            user_coords = (location.latitude, location.longitude)
            shop_coords = (SHOP_LAT, SHOP_LNG)
            distance_km = round(geodesic(shop_coords, user_coords).km, 2)  # Round to 2 decimals
            
            # Sanity check
            if distance_km > 50:
                print(f"[Distance Calc] WARNING: Geopy distance too far ({distance_km}km)")
                return 0, 0, f"Address location seems incorrect (calculated: {distance_km} KM). Please verify or use a landmark.", None, None
            
            print(f"⚠ [Distance Calc] Geopy GEODESIC: {distance_km} KM (straight-line)")
            return _calculate_price(distance_km, location.latitude, location.longitude)
        else:
            print(f"[Distance Calc] Geopy geocoding failed for: {search_query}")
            return 0, 0, "Address could not be located. Please provide a valid Indore address with landmark.", None, None
            
    except Exception as e:
        print(f"[Distance Calc] Geopy Exception: {e}")
        return 0, 0, f"Unable to calculate distance. Please try again or contact us.", None, None


def _calculate_price(distance_km, lat=None, lng=None):
    """Calculate delivery price based on distance."""
    # Ensure distance is rounded to 2 decimal places
    distance_km = round(float(distance_km), 2)
    price = 0
    
    if distance_km <= 3:
        price = 50
    elif distance_km <= 5:
        price = 70
    elif distance_km <= 7:
        price = 80
    else:
        return distance_km, 0, f"Out of delivery range. Distance: {distance_km} KM (max 7 KM).", lat, lng
    
    return distance_km, price, None, lat, lng




def save_csv_entry(filename, data, fieldnames):
    """
    Appends a dictionary row to a CSV file in /media/data/.
    Creates the file and directory if they don't exist.
    """
    import csv
    import os
    from django.conf import settings
    
    try:
        data_dir = os.path.join(settings.MEDIA_ROOT, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        file_path = os.path.join(data_dir, filename)
        file_exists = os.path.exists(file_path)
        
        with open(file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            # Ensure only relevant fields are written
            row = {field: data.get(field, '') for field in fieldnames}
            writer.writerow(row)
            
        return True, "Entry saved successfully."
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return False, str(e)
