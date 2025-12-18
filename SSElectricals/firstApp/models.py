from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

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
    display_name = models.CharField(max_length=150, blank=True, null=True, help_text="Publicly displayed name")
    
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STAFF = "STAFF", "Staff"
        USER = "USER", "User"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.USER)
    is_email_verified = models.BooleanField(default=False)
    
    # Order Tracking
    total_orders_count = models.PositiveIntegerField(default=0)
    free_delivery_used_count = models.PositiveIntegerField(default=0)
    
    # Theme Preference
    THEME_CHOICES = [
        ('light', 'Light Mode'),
        ('dark', 'Dark Mode'),
    ]
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')

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
    vendor = models.CharField(max_length=100, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_trending = models.BooleanField(default=False, help_text="Mark this product as trending")
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

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum([r.rating for r in reviews]) / len(reviews)
        return 0

    @property
    def review_count(self):
        return self.reviews.count()

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
    cancellation_reason = models.TextField(blank=True, null=True)
    
    # Delivery Info
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_otp = models.CharField(max_length=6, blank=True, null=True)
    free_delivery_applied = models.BooleanField(default=False, help_text="Whether free delivery was applied to this order")
    delivery_charge_status = models.CharField(max_length=20, default='ESTIMATED', choices=[('ESTIMATED', 'Estimated'), ('CONFIRMED', 'Confirmed')])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Receipt Fields (FY-based numbering for online orders)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True)
    financial_year = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., 2024-25")
    receipt_sequence = models.IntegerField(blank=True, null=True, help_text="Sequential number within FY")
    receipt_qr_code = models.ImageField(upload_to='order_qrcodes/', blank=True, null=True)
    receipt_qr_data = models.TextField(blank=True, null=True)
    receipt_generated_at = models.DateTimeField(blank=True, null=True)

    @property
    def grand_total(self):
        # Heuristic: If final_price was saved as just total_price (omitting delivery),
        # but there is a delivery charge, return the sum instead.
        if self.final_price:
            if self.final_price == self.total_price and self.delivery_charge > 0:
                 return self.total_price + self.delivery_charge
            return self.final_price
        return self.total_price + self.delivery_charge

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    
    @staticmethod
    def get_current_financial_year():
        """Get current calendar year (last 2 digits) - Jan to Dec"""
        from datetime import date
        return str(date.today().year)[2:]  # Returns '25' for 2025, '26' for 2026
    
    def generate_receipt_number(self):
        """Generate FY-based receipt number for order"""
        if not self.receipt_number and self.status in ['Confirmed', 'Out for Delivery', 'Delivered']:
            # Get current FY
            self.financial_year = self.get_current_financial_year()
            
            # Get last order receipt in this FY
            last_order = Order.objects.filter(
                financial_year=self.financial_year
            ).exclude(receipt_number__isnull=True).order_by('-receipt_sequence').first()
            
            seq = (last_order.receipt_sequence + 1) if last_order else 1
            
            self.receipt_sequence = seq
            self.receipt_number = f"ORD/{self.financial_year}/{seq:04d}"  # ORD prefix for orders
            self.receipt_generated_at = timezone.now()
            
            # Generate QR code data
            self.receipt_qr_data = (
                f"Order Receipt: {self.receipt_number}\n"
                f"Amount: ₹{self.grand_total}\n"
                f"Date: {self.created_at.strftime('%d-%m-%Y')}\n"
                f"Customer: {self.user.get_full_name() or self.user.username}"
            )
            
            self.save()
    
    def generate_receipt_qr_code(self):
        """Generate QR code image for order receipt"""
        if not self.receipt_qr_data:
            return
        
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            
            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(self.receipt_qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to file
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filename = f'order_receipt_{self.receipt_number.replace("/", "_")}.png'
            self.receipt_qr_code.save(filename, File(buffer), save=False)
            buffer.close()
            
            self.save()
        except ImportError:
            pass  # qrcode library not installed

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
         # Central Indore
    ('Rajwada', 'Rajwada'),
    ('Yashwant Ganj', 'Yashwant Ganj'),
    ('Juni Indore', 'Juni Indore'),
    ('Chhatribagh', 'Chhatribagh'),
    ('Malwa Mill', 'Malwa Mill'),
    ('Kesar Bagh', 'Kesar Bagh'),

    # East Indore
    ('Pardesipura', 'Pardesipura'),
    ('Gumasta Nagar', 'Gumasta Nagar'),
    ('Veena Nagar', 'Veena Nagar'),
    ('Usha Nagar', 'Usha Nagar'),
    ('Snehlataganj', 'Snehlataganj'),

    # West / Northwest Indore
    ('Palasia', 'Palasia'),
    ('Zanjeerwala Square', 'Zanjeerwala Square'),
    ('Scheme No. 74', 'Scheme No. 74'),
    ('Mahalaxmi Nagar', 'Mahalaxmi Nagar'),
    ('Vijay Nagar', 'Vijay Nagar'),
    ('Nipania', 'Nipania'),
    ('Bapat Square', 'Bapat Square'),
    ('MR10', 'MR10'),
    ('Silicon City', 'Silicon City'),

    # North Indore
    ('Patnipura', 'Patnipura'),
    ('Hawa Bangla', 'Hawa Bangla'),
    ('Tilak Nagar', 'Tilak Nagar'),

    # South Indore
    ('Rajendra Nagar', 'Rajendra Nagar'),
    ('Annapurna Nagar', 'Annapurna Nagar'),
    ('Manik Bagh', 'Manik Bagh'),
    ('Kanadia Road', 'Kanadia Road'),

    # Residential Colonies
    ('Sukhliya', 'Sukhliya'),
    ('Abhinandan Nagar', 'Abhinandan Nagar'),
    ('LIG Colony', 'LIG Colony'),
    ('Prime City', 'Prime City'),
    ('Royal Bungalow City', 'Royal Bungalow City'),
    ('Sundar Nagar', 'Sundar Nagar'),
    ('Gauri Nagar', 'Gauri Nagar'),
    ('Luv Kush', 'Luv Kush'),

    # Fallback
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

# 7. Product Review System
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='review_images/', null=True, blank=True, help_text="Optional: Upload a photo of the product")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s review on {self.product.name}"

# 8. Daily Sales Entry
# 8. Daily Sales Entry
class DailySales(models.Model):
    REMARK_CHOICES = [
        ('NILL', 'NILL'),
        ('Shop Closed', 'Shop Closed'),
        ('Other', 'Other'),
    ]

    date = models.DateField()
    day = models.CharField(max_length=20)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    online_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cash_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Optional charges - default to 0, nullable to support NULL when cleared
    labor_charge = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        null=True, 
        blank=True,
        help_text="Labor charges for the day (optional)"
    )
    delivery_charge = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        null=True, 
        blank=True,
        help_text="Delivery charges collected (optional)"
    )
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remark = models.CharField(max_length=20, choices=REMARK_CHOICES, default='NILL')
    other_remark = models.TextField(blank=True, null=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['date'], name='unique_daily_sales_date')
        ]

    def save(self, *args, **kwargs):
        # Subtotal calculation: Online + Cash (labor and delivery NOT included)
        if not self.subtotal:
            self.subtotal = self.online_received + self.cash_received
        if not self.day and self.date:
            self.day = self.date.strftime('%A')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sales for {self.date} ({self.day})"

# 9. Daily Investment / Expenditure
class DailyExpenditure(models.Model):
    date = models.DateField()
    day = models.CharField(max_length=20)
    
    # Combined online and cash amounts in single entry
    online_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        null=True,
        blank=True,
        help_text="Online expenses for the day"
    )
    cash_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        null=True,
        blank=True,
        help_text="Cash expenses for the day"
    )
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Auto-calculated total (Online + Cash)"
    )
    
    description = models.TextField()
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            # One entry per day with combined online and cash
            models.UniqueConstraint(fields=['date'], name='unique_daily_expenditure_date')
        ]

    def save(self, *args, **kwargs):
        # Auto-calculate day
        if self.date:
            self.day = self.date.strftime('%A')
        
        # Auto-calculate total (Online + Cash)
        online = self.online_amount or 0
        cash = self.cash_amount or 0
        self.total = online + cash
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Expense on {self.date}: ₹{self.total}"

# 10. Wishlist
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') # Prevent duplicate products in wishlist for a user

    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.name}"

# 11. Purchase Entry (Inventory Update)
class PurchaseEntry(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchase_entries')
    vendor = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2) # Cost per unit
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.total_cost and self.quantity and self.purchase_price:
            self.total_cost = self.quantity * self.purchase_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Purchase: {self.product.name} ({self.quantity} qty)"

# 12. Email Logging System
class EmailLog(models.Model):
    """Track all email communications for audit and retry purposes"""
    EMAIL_TYPE_CHOICES = [
        ('ORDER_STATUS', 'Order Status Update'),
        ('ORDER_RECEIPT', 'Order Receipt'),
        ('DELIVERY_OTP', 'Delivery OTP'),
        ('ORDER_DELIVERED', 'Order Delivered'),
        ('APPOINTMENT_STATUS', 'Appointment Status Update'),
        ('APPOINTMENT_COMPLETE', 'Appointment Complete'),
        ('OTP_VERIFICATION', 'OTP Verification'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('RETRY', 'Retry'),
    ]
    
    email_type = models.CharField(max_length=30, choices=EMAIL_TYPE_CHOICES)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Reference fields
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='email_logs')
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email_type', 'recipient']),
        ]
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient} - {self.status}"

# 13. Financial Validation & Audit Log
class FinancialValidationLog(models.Model):
    """
    Logs any accidental attempts to update financial data from order workflows.
    
    CRITICAL BUSINESS RULE:
    ======================= 
    Orders should NEVER automatically update financial metrics.
    This model logs violations of this rule for audit purposes.
    """
    
    VIOLATION_TYPE_CHOICES = [
        ('AUTO_REVENUE_UPDATE', 'Attempted Auto Revenue Update'),
        ('AUTO_SALES_UPDATE', 'Attempted Auto Sales Update'),
        ('ORDER_TO_FINANCE', 'Order Data Used in Finance Calculation'),
        ('OTHER', 'Other Violation'),
    ]
    
    violation_type = models.CharField(max_length=30, choices=VIOLATION_TYPE_CHOICES)
    description = models.TextField(help_text="Details of the attempted violation")
    source_module = models.CharField(max_length=100, help_text="Module/function that attempted the update")
    
    # Reference fields
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking
    detected_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-detected_at']
        verbose_name = "Financial Validation Log"
        verbose_name_plural = "Financial Validation Logs"
        indexes = [
            models.Index(fields=['violation_type', 'detected_at']),
        ]
    
    def __str__(self):
        return f"{self.violation_type} - {self.detected_at.strftime('%Y-%m-%d %H:%M')}"

# 14. One-Tap Email Login Tokens
class EmailLoginToken(models.Model):
    """
    Secure tokens for one-tap email login.
    Regular users only - NOT for admin/staff.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='email_login_tokens'
    )
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'is_used']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Login token for {self.user.email} - {'Used' if self.is_used else 'Active'}"
    
    @staticmethod
    def generate_token():
        """Generate a cryptographically secure random token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        """Check if token is still valid"""
        if self.is_used:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
    
    def mark_used(self):
        """Mark token as used to prevent replay attacks"""
        self.is_used = True
        self.save()


# 15. Offline Receipt / Manual Billing System
class OfflineReceipt(models.Model):
    """
    Offline receipts for walk-in customers - ISOLATED from online sales.
    Does NOT affect daily sales, expenses, or analytics.
    Enhanced with FY numbering, PDF export, and void/correction workflow.
    """
    
    # Receipt Status Choices
    class ReceiptStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        VOID = 'VOID', 'Void'
        CORRECTED = 'CORRECTED', 'Corrected'
    
    # Unique Receipt Identifier (FY-based)
    receipt_number = models.CharField(max_length=50, unique=True, editable=False, db_index=True)
    financial_year = models.CharField(max_length=10, help_text="e.g., 2024-25", editable=False)
    sequence_number = models.IntegerField(help_text="Sequential number within FY", editable=False)
    
    # Receipt Status
    status = models.CharField(
        max_length=20,
        choices=ReceiptStatus.choices,
        default=ReceiptStatus.ACTIVE
    )
    
    # Void Information
    void_reason = models.TextField(blank=True, null=True, help_text="Reason for voiding receipt")
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voided_receipts',
        help_text="Admin who voided this receipt"
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    
    # Correction Reference
    original_receipt = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrections',
        help_text="Original receipt if this is a correction"
    )
    corrected_by_receipt = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrected_from',
        help_text="Corrected receipt reference"
    )
    
    # Buyer Information
    buyer_name = models.CharField(max_length=200)
    buyer_email = models.EmailField(blank=True, null=True, help_text="Optional - links receipt to user account")
    buyer_phone = models.CharField(max_length=15, blank=True, null=True)
    buyer_address = models.TextField(blank=True, null=True, help_text="No house number required")
    
    # Shop Information (for receipt header)
    shop_name = models.CharField(max_length=200, default="Shiv Shakti Electrical")
    shop_address = models.TextField(default="Indore, Madhya Pradesh")
    shop_phone = models.CharField(max_length=15, default="+91 9993149226")
    shop_gst = models.CharField(max_length=50, blank=True, null=True)
    
    # Financial Details (Manual Entry)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="GST/Tax")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # QR Code Data
    qr_code_data = models.TextField(blank=True, null=True, help_text="Data encoded in receipt QR code")
    qr_code_image = models.ImageField(upload_to='receipt_qrcodes/', blank=True, null=True)
    
    # PDF Storage
    pdf_file = models.FileField(upload_to='receipt_pdfs/', blank=True, null=True)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_receipts',
        help_text="Admin who created this receipt"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Offline Receipt"
        verbose_name_plural = "Offline Receipts"
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['financial_year', 'sequence_number']),
            models.Index(fields=['buyer_email']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
        unique_together = [['financial_year', 'sequence_number']]
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.buyer_name} ({self.get_status_display()})"
    
    @staticmethod
    def get_current_financial_year():
        """Get current calendar year (last 2 digits) - Jan to Dec"""
        from datetime import date
        return str(date.today().year)[2:]  # Returns '25' for 2025, '26' for 2026
    
    @staticmethod
    def get_next_sequence_number(financial_year):
        """Get next sequence number for given FY"""
        last_receipt = OfflineReceipt.objects.filter(
            financial_year=financial_year
        ).order_by('-sequence_number').first()
        
        if last_receipt:
            return last_receipt.sequence_number + 1
        return 1
    
    def save(self, *args, **kwargs):
        """Auto-generate FY-based receipt number on creation"""
        if not self.receipt_number:
            # Get current FY
            self.financial_year = self.get_current_financial_year()
            
            # Get next sequence number
            self.sequence_number = self.get_next_sequence_number(self.financial_year)
            
            # Generate receipt number: SS/25/0001 (year/sequence)
            prefix = "SS"  # Shop initials (configurable)
            self.receipt_number = f"{prefix}/{self.financial_year}/{self.sequence_number:04d}"
        
        # Auto-generate QR code data
        if not self.qr_code_data:
            self.qr_code_data = (
                f"Receipt: {self.receipt_number}\n"
                f"Amount: ₹{self.grand_total}\n"
                f"Date: {timezone.now().strftime('%d-%m-%Y')}\n"
                f"Shop: {self.shop_name}"
            )
        
        super().save(*args, **kwargs)
    
    def void_receipt(self, admin_user, reason):
        """Mark receipt as void"""
        if self.status == self.ReceiptStatus.VOID:
            raise ValueError("Receipt is already void")
        
        self.status = self.ReceiptStatus.VOID
        self.void_reason = reason
        self.voided_by = admin_user
        self.voided_at = timezone.now()
        self.save()
    
    def create_correction(self, admin_user):
        """Create a corrected copy of this receipt"""
        # Create new receipt as correction
        corrected = OfflineReceipt()
        corrected.buyer_name = self.buyer_name
        corrected.buyer_email = self.buyer_email
        corrected.buyer_phone = self.buyer_phone
        corrected.buyer_address = self.buyer_address
        corrected.shop_name = self.shop_name
        corrected.shop_address = self.shop_address
        corrected.shop_phone = self.shop_phone
        corrected.shop_gst = self.shop_gst
        corrected.subtotal = self.subtotal
        corrected.tax_amount = self.tax_amount
        corrected.discount_amount = self.discount_amount
        corrected.grand_total = self.grand_total
        corrected.original_receipt = self
        corrected.created_by = admin_user
        corrected.status = self.ReceiptStatus.CORRECTED
        corrected.save()
        
        # Copy items
        for item in self.items.all():
            ReceiptItem.objects.create(
                receipt=corrected,
                item_name=item.item_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                description=item.description
            )
        
        # Mark this receipt as having a correction
        self.corrected_by_receipt = corrected
        self.save()
        
        return corrected
    
    def get_linked_user(self):
        """Get user account linked via email"""
        if self.buyer_email:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                return User.objects.get(email=self.buyer_email)
            except User.DoesNotExist:
                return None
        return None
    
    def is_editable(self):
        """Check if receipt can be edited"""
        return self.status == self.ReceiptStatus.ACTIVE and not self.corrected_by_receipt
    
    def generate_qr_code(self):
        """Generate QR code image for receipt"""
        try:
            import qrcode
            from io import BytesIO
            from django.core.files import File
            
            # Create QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(self.qr_code_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to file
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filename = f'receipt_{self.receipt_number.replace("/", "_")}.png'
            self.qr_code_image.save(filename, File(buffer), save=False)
            buffer.close()
            
            self.save()
        except ImportError:
            pass  # qrcode library not installed



class ReceiptItem(models.Model):
    """
    Line items for offline receipts
    """
    receipt = models.ForeignKey(
        OfflineReceipt,
        on_delete=models.CASCADE,
        related_name='items'
    )
    item_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Item description/notes
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = "Receipt Item"
        verbose_name_plural = "Receipt Items"
    
    def __str__(self):
        return f"{self.item_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate line total"""
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
