import os
import django
import sys

# Add the project root to the python path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SSElectricals.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = 'admin'
password = 'password123'
email = 'admin@example.com'
phone = '9999999999' # Since phone_number is required and unique

try:
    if User.objects.filter(username=username).exists():
        print(f"User '{username}' already exists. Resetting password.")
        u = User.objects.get(username=username)
        u.set_password(password)
        u.save()
    elif User.objects.filter(phone_number=phone).exists():
        print(f"User with phone '{phone}' already exists. Resetting password.")
        u = User.objects.get(phone_number=phone)
        u.set_password(password)
        u.save()
    else:
        print(f"Creating user '{username}'.")
        # Ensure phone number is provided if it's a required field in CustomUser
        User.objects.create_superuser(username=username, email=email, password=password, phone_number=phone)

    print(f"Superuser credentials:\nUsername: {username}\nPassword: {password}\nPhone: {phone}")

except Exception as e:
    print(f"Error: {e}")
