from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# 1. Authentication System
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True, null=True) # Keeping for backward compatibility
    house_number = models.CharField(max_length=50, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True, default='Indore')
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return self.phone_number

# 2. Product Management
class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Fan', 'Fan'),
        ('Switches', 'Switches'),
        ('Wires', 'Wires'),
        ('LEDs', 'LEDs'),
        ('Motors', 'Motors'),
        ('Tools', 'Tools'),
        ('Others', 'Others'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    brand = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='product_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.image:
            try:
                from PIL import Image
                img = Image.open(self.image.path)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except Exception as e:
                pass

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        return self.discount_price if self.discount_price else self.price

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.image:
            try:
                from PIL import Image
                img = Image.open(self.image.path)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except Exception as e:
                pass

    def __str__(self):
        return f"Image for {self.product.name}"



# 3. Shopping Features
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.product.final_price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    address = models.TextField()
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    # Pricing
    total_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Sum of product prices")
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Final price confirmed by admin")
    
    # Delivery Info
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_otp = models.CharField(max_length=6, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"

# 4. Admin Session Management
class AdminSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"

class AdminActivityLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    MODULE_CHOICES = [
        ('PRODUCT', 'Product'),
        ('CATEGORY', 'Category'),
        ('ORDER', 'Order'),
        ('USER', 'User'),
        ('SESSION', 'Session'),
        ('CART', 'Cart'),
    ]

    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.admin.username} - {self.action} on {self.module} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

# 5. OTP Authentication


class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    max_retries = models.IntegerField(default=3)
    retry_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'created_at']),
        ]

    def __str__(self):
        return f"{self.email} - {self.otp}"

    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))

    def is_valid(self):
        """Check if OTP is still valid (within 5 minutes)"""
        from django.utils import timezone
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(minutes=5)
        return timezone.now() < expiry_time and not self.is_verified

    def verify(self, entered_otp):
        """Verify the OTP"""
        if not self.is_valid():
            return False, "OTP has expired"
        
        if self.retry_count >= self.max_retries:
            return False, "Maximum retry attempts exceeded"
        
        if self.otp == entered_otp:
            self.is_verified = True
            self.save()
            return True, "OTP verified successfully"
        else:
            self.retry_count += 1
            self.save()
            return False, f"Invalid OTP. {self.max_retries - self.retry_count} attempts remaining"

# 6. Appointment System
class Appointment(models.Model):
    SERVICE_CHOICES = [
        ('CCTV Installation', 'CCTV Installation'),
        ('Electrical Wiring / Short Circuit', 'Electrical Wiring / Short Circuit'),
        ('Fan / Motor Repair', 'Fan / Motor Repair'),
        ('Fridge Repair', 'Fridge Repair'),
        ('Geyser Repair', 'Geyser Repair'),
        ('LED / Tube Light Repair', 'LED / Tube Light Repair'),
        ('Underground Wiring', 'Underground Wiring'),
        ('Washing Machine Repair', 'Washing Machine Repair'),
        ('Other Appliance Repair', 'Other Appliance Repair'),

    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    CITY_CHOICES = [
        ('Indore', 'Indore'),
    ]

    AREA_CHOICES = [
        ('Abhinandan Nagar', 'Abhinandan Nagar'),
        ('Bapat Square', 'Bapat Square'),
        ('Bhawarkua', 'Bhawarkua'),
        ('Gauri Nagar', 'Gauri Nagar'),
        ('Khajrana', 'Khajrana'),
        ('LIG Colony', 'LIG Colony'),
        ('Luv Kush', 'Luv Kush'),
        ('MR10', 'MR10'),
        ('Malwa Mill', 'Malwa Mill'),
        ('Nehru Nagar', 'Nehru Nagar'),
        ('Nipania', 'Nipania'),
        ('Palasia', 'Palasia'),
        ('Pardesipura', 'Pardesipura'),
        ('Prime City', 'Prime City'),
        ('Rajendra Nagar', 'Rajendra Nagar'),
        ('Rajwada', 'Rajwada'),
        ('Royal Bungalow City', 'Royal Bungalow City'),
        ('Scheme No. 74', 'Scheme No. 74'),
        ('Sukhliya', 'Sukhliya'),
        ('Sundar Nagar', 'Sundar Nagar'),
        ('Veena Nagar', 'Veena Nagar'),
        ('Vijay Nagar', 'Vijay Nagar'),
        ('Other', 'Other region'),
    ]

    # Link to user if logged in (optional but good for history)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    # Detailed Address Fields
    pincode = models.CharField(max_length=6, default='452001')
    house_number = models.CharField(max_length=50, default='')
    address_line1 = models.CharField(max_length=255, default='')
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    # Keeping original address field for backward compatibility or full address storage if needed
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, choices=CITY_CHOICES, default='Indore')
    area = models.CharField(max_length=50, default='Other')
    
    service_type = models.CharField(max_length=100, choices=SERVICE_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    problem_description = models.TextField()
    
    visiting_charge = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    extra_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    cancellation_reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.service_type} ({self.date})"

    @property
    def total_charge(self):
        return self.visiting_charge + self.extra_charge
