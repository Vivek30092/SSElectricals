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
            masked_local = local_part[0] + '*' * 5 + local_part[-1]
            
        return f"{masked_local}@{domain}"
    except:
        return email

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
    Calculate distance using Google Maps API, falling back to Geopy (OpenStreetMap) if necessary.
    Returns: (distance_km, price, error_message, latitude, longitude)
    """
    api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
    
    # Try Google Maps API first if key exists
    if api_key:
        try:
            origin = f"{SHOP_LAT},{SHOP_LNG}"
            destination = user_address
            # Note: Distance Matrix doesn't return destination coords. 
            # If strictly needed, we'd need Geocoding API here. 
            # For now returning None, None for coords if strictly using Distance Matrix.
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={api_key}"
            
            response = requests.get(url)
            data = response.json()
            
            if data['status'] == 'OK':
                if 'rows' in data and data['rows']:
                    element = data['rows'][0]['elements'][0]
                    if element['status'] == 'OK':
                        distance_value = element['distance']['value']
                        distance_km = distance_value / 1000.0
                        return _calculate_price(distance_km) # Returns (dist, price, err, None, None) by default logic below? No, need to update _calculate_price
                    else:
                        pass
                else:
                    pass
            elif data['status'] == 'REQUEST_DENIED':
                print("Google Maps API Request Denied. Falling back to Geopy.")
                # Fallback to Geopy
            else:
                 return 0, 0, f"Distance API Error: {data['status']}", None, None
        except Exception as e:
            print(f"Google Maps API Error: {e}")
            # Fallback to Geopy

    # Fallback: Geopy (Nominatim)
    try:
        from geopy.geocoders import Nominatim
        
        # Initialize with user agent
        geolocator = Nominatim(user_agent="sselectricals_app_v2", timeout=10)
        
        # 1. Structured Query (More reliable)
        # We try to extract components if the input string is structured specifically, 
        # but since 'user_address' is often a single string, we might just append 'Indore'
        
        search_query = user_address
        if "indore" not in search_query.lower():
            search_query += ", Indore"
        if "madhya pradesh" not in search_query.lower():
            search_query += ", Madhya Pradesh"
        if "india" not in search_query.lower():
            search_query += ", India"

        # 2. Viewbox Restriction (Box around Indore)
        # Approximate box: Top-Left (23.0, 75.5), Bottom-Right (22.5, 76.2)
        # This helps ignore results from other states/countries
        viewbox = [
            (23.0, 75.5), # North-West
            (22.5, 76.2)  # South-East
        ]
        
        location = geolocator.geocode(search_query, viewbox=viewbox, bounded=True)
        
        # 3. Validation
        if location:
            # Check if really in Indore (redundant if bounded=True works, but good safety)
            # Or just check distance bounds immediately
            pass
            
            user_coords = (location.latitude, location.longitude)
            shop_coords = (SHOP_LAT, SHOP_LNG)
            distance_km = geodesic(shop_coords, user_coords).km
            
            # Sanity Check: If distance > 100km, something is wrong with geocoding result
            if distance_km > 50:
                 print(f"Geocoding Warning: Found location too far ({distance_km}km). Query: {search_query}, Result: {location.address}")
                 return 0, 0, f"We could not locate this address precisely in Indore. (Distance calculated: {distance_km:.2f} KM). Please provide a landmark or use the map pin.", None, None

            return _calculate_price(distance_km, location.latitude, location.longitude)
        else:
            print(f"Geocoding Failed: No location found for {search_query}")
            # Try a broader search without bounds just in case, but usually dangerous
            return 0, 0, "Address could not be located on map. Please ensure valid area/landmark inside Indore.", None, None
            
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return 0, 0, f"Error calculating distance: {str(e)}", None, None

def _calculate_price(distance_km, lat=None, lng=None):
    distance_km = round(distance_km, 2)
    price = 0
    if distance_km <= 3:
        price = 50
    elif distance_km <= 7:
        price = 70
    else:
        return distance_km, 0, f"Delivery available only within 7 KM. Your distance: {distance_km} KM.", lat, lng
    
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
