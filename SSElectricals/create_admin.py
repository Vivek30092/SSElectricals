import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SSElectricals.settings')
django.setup()

from firstApp.models import CustomUser

# Check if superuser exists
phone = '7828659551'
if CustomUser.objects.filter(phone_number=phone).exists():
    print(f"User with phone {phone} already exists!")
    user = CustomUser.objects.get(phone_number=phone)
    print(f"Username: {user.phone_number}")
    print(f"Email: {user.email}")
    print(f"Is superuser: {user.is_superuser}")
    print("\nTo reset password, delete the user first:")
    print(f"  CustomUser.objects.filter(phone_number='{phone}').delete()")
else:
    # Create superuser
    user = CustomUser.objects.create_superuser(
        phone_number=phone,
        username=phone,  # Set username same as phone
        email='vivekkumarc934@gmail.com',
        password='v1430',
        first_name='vivek', 
        last_name='choudhary'
    )
    print("Superuser created successfully!")
    print(f"Phone (Username): {phone}")
    print(f"Password: v1430")
    print(f"\nLogin at: http://127.0.0.1:8000/admin/")
