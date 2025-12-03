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


