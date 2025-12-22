from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone

# 1. Authentication System
class CustomUser(AbstractUser):
    # Override email to make it unique (required for USERNAME_FIELD)
    email = models.EmailField(unique=True)
    
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email or self.username

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
    description = models.TextField()  # Long description (HTML-enabled)
    short_description = models.CharField(max_length=200, blank=True, default='', help_text="Brief summary for product cards (max 200 chars)")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    brand = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='product_images/')
    vendor = models.CharField(max_length=100, blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_trending = models.BooleanField(default=False, help_text="Mark this product as trending")
    is_visible_on_website = models.BooleanField(default=False, help_text="Show this product on the website (default: hidden)")
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
    
    # TASK 1: Stock status properties
    @property
    def is_in_stock(self):
        """Returns True if product is in stock, False otherwise"""
        return self.stock_quantity > 0
    
    @property
    def stock_status(self):
        """Returns 'In Stock' or 'Out of Stock' based on quantity"""
        return "In Stock" if self.is_in_stock else "Out of Stock"
    
    # TASK 2: Description helper
    def get_short_description(self):
        """Returns short description, or truncated long description if short is empty"""
        if self.short_description:
            return self.short_description
        # Fallback: extract first 160 chars from description (strip HTML)
        import re
        plain_text = re.sub('<[^<]+?>', '', self.description)
        return plain_text[:160] + '...' if len(plain_text) > 160 else plain_text

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
    # Enquiry-based purchase flow status choices
    STATUS_CHOICES = [
        ('Pending Enquiry', 'Pending Enquiry'),  # User submitted enquiry (default)
        ('Price Shared', 'Price Shared'),        # Admin has shared pricing with user
        ('Confirmed', 'Confirmed'),              # User/Admin confirmed order
        ('Ready for Pickup', 'Ready for Pickup'), # For pickup orders - ready at shop
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    
    # Order type to distinguish enquiry-based vs direct (legacy)
    ORDER_TYPE_CHOICES = [
        ('enquiry', 'Enquiry-Based Order'),
        ('direct', 'Direct Order (Legacy)'),
    ]
    
    # Fulfillment type - how customer will receive the order
    FULFILLMENT_CHOICES = [
        ('PICKUP', 'Pick from Store'),
        ('DELIVERY', 'Online Delivery'),
    ]
    
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE_DELIVERY', 'Online (Pay at Delivery using QR code)'),
    ]


    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    address = models.TextField(blank=True, null=True)  # Optional for pickup orders
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    # Fulfillment Type - Pickup from Store OR Online Delivery
    fulfillment_type = models.CharField(
        max_length=20, 
        choices=FULFILLMENT_CHOICES, 
        default='DELIVERY',
        help_text="How customer will receive the order"
    )
    
    # Order Type
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='enquiry')
    
    # Pricing (Admin-controlled for enquiry-based orders)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                       help_text="Admin-entered product price (hidden until confirmed)")
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, 
                                       help_text="Final price confirmed by admin")
    pricing_confirmed = models.BooleanField(default=False, 
                                             help_text="True when admin has entered and confirmed pricing")
    cancellation_reason = models.TextField(blank=True, null=True)
    
    # User notes/requirements for enquiry
    user_notes = models.TextField(blank=True, null=True, 
                                   help_text="Special requirements or notes from user")
    
    # Delivery Info
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_otp = models.CharField(max_length=6, blank=True, null=True)
    free_delivery_applied = models.BooleanField(default=False, help_text="Whether free delivery was applied to this order")
    delivery_charge_status = models.CharField(max_length=20, default='ESTIMATED', choices=[('ESTIMATED', 'Estimated'), ('CONFIRMED', 'Confirmed')])
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending Enquiry')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='COD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Receipt Fields (FY-based numbering for online orders)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True, db_index=True)
    financial_year = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., 2024-25")
    receipt_sequence = models.IntegerField(blank=True, null=True, help_text="Sequential number within FY")
    receipt_qr_code = models.ImageField(upload_to='order_qrcodes/', blank=True, null=True)
    receipt_qr_data = models.TextField(blank=True, null=True)
    receipt_generated_at = models.DateTimeField(blank=True, null=True)

    @property
    def grand_total(self):
        """
        Returns the grand total for the order.
        For enquiry orders without confirmed pricing, returns None.
        """
        # Enquiry orders without pricing confirmation - return None
        if self.order_type == 'enquiry' and not self.pricing_confirmed:
            return None
        
        # Use final price if available
        if self.final_price:
            if self.final_price == self.total_price and self.delivery_charge > 0:
                 return self.total_price + self.delivery_charge
            return self.final_price
        return self.total_price + self.delivery_charge
    
    @property
    def is_enquiry_pending(self):
        """Returns True if this is an enquiry order awaiting price confirmation."""
        return self.order_type == 'enquiry' and not self.pricing_confirmed
    
    @property
    def price_display_status(self):
        """Returns status message for price display."""
        if self.order_type == 'enquiry':
            if not self.pricing_confirmed:
                return "Price confirmation pending"
            elif self.status == 'Price Shared':
                return "Awaiting your approval"
        return "Confirmed"

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

# 6a. Dynamic Service Types (Admin can add/remove) with Distance-Based Pricing
class ServiceType(models.Model):
    """
    Dynamic service types that admin can add/remove.
    Includes distance-based pricing configuration.
    """
    PRICING_MODE_CHOICES = [
        ('fixed', 'Fixed Price (Auto-applied)'),
        ('confirm', 'Confirm Later (Admin will confirm)'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-tools', help_text="Font Awesome icon class")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Order in dropdown (lower = first)")
    
    # Pricing Mode
    pricing_mode = models.CharField(max_length=20, choices=PRICING_MODE_CHOICES, default='fixed',
                                     help_text="Fixed: Show price. Confirm: Admin confirms price after booking.")
    
    # Distance-Based Pricing (in Rupees)
    default_charge = models.DecimalField(max_digits=10, decimal_places=2, default=300.00,
                                          help_text="Fallback/default charge if distance not matched")
    charge_within_500m = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                              help_text="Charge for within 500 meters (optional)")
    charge_within_1km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                             help_text="Charge for within 1 KM (optional)")
    charge_within_3km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                             help_text="Charge for within 3 KM (optional)")
    charge_within_5km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                             help_text="Charge for within 5 KM (optional)")
    charge_within_7km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                             help_text="Charge for within 7 KM (optional)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Service Type'
        verbose_name_plural = 'Service Types'
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_choices(cls):
        """Get active service types as choices for forms."""
        return [(s.id, s.name) for s in cls.objects.filter(is_active=True).order_by('display_order', 'name')]
    
    @classmethod
    def get_active_services(cls):
        """Get all active services for booking page."""
        return cls.objects.filter(is_active=True).order_by('display_order', 'name')
    
    def get_charge_for_distance(self, distance_km):
        """
        Get the appropriate charge based on distance.
        Returns (charge, is_confirmed) tuple.
        """
        if self.pricing_mode == 'confirm':
            return (None, False)  # Price to be confirmed
        
        # Check distance ranges (smallest to largest)
        if distance_km is not None:
            if distance_km <= 0.5 and self.charge_within_500m:
                return (float(self.charge_within_500m), True)
            elif distance_km <= 1 and self.charge_within_1km:
                return (float(self.charge_within_1km), True)
            elif distance_km <= 3 and self.charge_within_3km:
                return (float(self.charge_within_3km), True)
            elif distance_km <= 5 and self.charge_within_5km:
                return (float(self.charge_within_5km), True)
            elif distance_km <= 7 and self.charge_within_7km:
                return (float(self.charge_within_7km), True)
        
        # Fallback to default charge
        return (float(self.default_charge), True)


# 6b. Distance-Based Pricing Zones
class DistanceZone(models.Model):
    """
    Distance ranges from shop for pricing.
    Admin can configure charges for each distance range.
    """
    ZONE_CODES = [
        ('VERY_NEAR', 'Very Near (0-500m)'),
        ('NEAR', 'Near (0-3 KM)'),
        ('MEDIUM', 'Medium (3-5 KM)'),
        ('FAR', 'Far (5-7 KM)'),
        ('VERY_FAR', 'Very Far (7+ KM)'),
    ]
    
    code = models.CharField(max_length=20, choices=ZONE_CODES, unique=True)
    min_distance_km = models.DecimalField(max_digits=5, decimal_places=2, help_text="Minimum distance in KM")
    max_distance_km = models.DecimalField(max_digits=5, decimal_places=2, help_text="Maximum distance in KM (use 999 for unlimited)")
    base_charge = models.DecimalField(max_digits=10, decimal_places=2, default=200.00,
                                       help_text="Base visiting/inspection charge for this distance")
    is_active = models.BooleanField(default=True)
    requires_confirmation = models.BooleanField(default=False, 
                                                 help_text="If true, staff will confirm pricing manually")
    notes = models.CharField(max_length=200, blank=True, help_text="Notes shown to user (e.g., 'Contact for quote')")
    
    class Meta:
        ordering = ['min_distance_km']
        verbose_name = 'Distance Zone'
        verbose_name_plural = 'Distance Zones'
    
    def __str__(self):
        return f"{self.get_code_display()} - ₹{self.base_charge}"
    
    @classmethod
    def get_zone_for_distance(cls, distance_km):
        """Get the appropriate zone for a given distance."""
        try:
            return cls.objects.filter(
                min_distance_km__lte=distance_km,
                max_distance_km__gt=distance_km,
                is_active=True
            ).first()
        except cls.DoesNotExist:
            return None


# 6c. Area to Region Mapping (for showing cities in regions)
class AreaRegion(models.Model):
    """
    Maps specific areas/localities to regions.
    Helps show users which areas are covered.
    """
    REGION_CHOICES = [
        ('CENTRAL', 'Central Indore'),
        ('EAST', 'East Indore'),
        ('WEST', 'West Indore'),
        ('NORTH', 'North Indore'),
        ('SOUTH', 'South Indore'),
        ('RESIDENTIAL', 'Residential Colonies'),
    ]
    
    area_name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=20, choices=REGION_CHOICES)
    pincode = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['region', 'area_name']
        verbose_name = 'Area Region'
        verbose_name_plural = 'Area Regions'
    
    def __str__(self):
        return f"{self.area_name} ({self.get_region_display()})"
    
    @classmethod
    def get_areas_by_region(cls):
        """Get areas grouped by region."""
        from collections import defaultdict
        areas_by_region = defaultdict(list)
        for area in cls.objects.filter(is_active=True):
            areas_by_region[area.get_region_display()].append(area.area_name)
        return dict(areas_by_region)


# 6d. Service Pricing System (Updated)
class ServicePrice(models.Model):
    """
    Stores service pricing based on service type and area zone.
    Admin can set different prices for different areas.
    """
    SERVICE_TYPE_CHOICES = [
        # Sorted Alphabetically (Other at end)
        ('AC Installation', 'AC Installation'),
        ('CCTV Installation', 'CCTV Installation'),
        ('Cooler Repair', 'Cooler Repair'),
        ('Electrical Wiring / Short Circuit', 'Electrical Wiring / Short Circuit'),
        ('Fan / Motor Repair', 'Fan / Motor Repair'),
        ('Fan Installation', 'Fan Installation'),
        ('Fridge Repair', 'Fridge Repair'),
        ('Geyser Installation', 'Geyser Installation'),
        ('Geyser Repair', 'Geyser Repair'),
        ('LED / Tube Light Repair', 'LED / Tube Light Repair'),
        ('TV Installation', 'TV Installation'),
        ('Underground Wiring', 'Underground Wiring'),
        ('Washing Machine Repair', 'Washing Machine Repair'),
        ('Other Appliance Repair', 'Other Appliance Repair'),
    ]
    
    ZONE_CHOICES = [
        ('CENTRAL', 'Central Indore (Rajwada, Juni Indore, etc.)'),
        ('EAST', 'East Indore (Pardesipura, Gumasta Nagar, etc.)'),
        ('WEST', 'West/Northwest Indore (Vijay Nagar, Nipania, etc.)'),
        ('NORTH', 'North Indore (Patnipura, Hawa Bangla, etc.)'),
        ('SOUTH', 'South Indore (Rajendra Nagar, Kanadia Road, etc.)'),
        ('RESIDENTIAL', 'Residential Colonies (Sukhliya, LIG, etc.)'),
        ('OTHER', 'Other Areas'),
    ]
    
    # Map areas to zones
    AREA_TO_ZONE = {
        # Central
        'Rajwada': 'CENTRAL', 'Yashwant Ganj': 'CENTRAL', 'Juni Indore': 'CENTRAL',
        'Chhatribagh': 'CENTRAL', 'Malwa Mill': 'CENTRAL', 'Kesar Bagh': 'CENTRAL',
        # East
        'Pardesipura': 'EAST', 'Gumasta Nagar': 'EAST', 'Veena Nagar': 'EAST',
        'Usha Nagar': 'EAST', 'Snehlataganj': 'EAST',
        # West/Northwest
        'Palasia': 'WEST', 'Zanjeerwala Square': 'WEST', 'Scheme No. 74': 'WEST',
        'Mahalaxmi Nagar': 'WEST', 'Vijay Nagar': 'WEST', 'Nipania': 'WEST',
        'Bapat Square': 'WEST', 'MR10': 'WEST', 'Silicon City': 'WEST',
        # North
        'Patnipura': 'NORTH', 'Hawa Bangla': 'NORTH', 'Tilak Nagar': 'NORTH',
        # South
        'Rajendra Nagar': 'SOUTH', 'Annapurna Nagar': 'SOUTH', 'Manik Bagh': 'SOUTH',
        'Kanadia Road': 'SOUTH',
        # Residential
        'Sukhliya': 'RESIDENTIAL', 'Abhinandan Nagar': 'RESIDENTIAL', 'LIG Colony': 'RESIDENTIAL',
        'Prime City': 'RESIDENTIAL', 'Royal Bungalow City': 'RESIDENTIAL', 'Sundar Nagar': 'RESIDENTIAL',
        'Gauri Nagar': 'RESIDENTIAL', 'Luv Kush': 'RESIDENTIAL',
    }
    
    service_type = models.CharField(max_length=100, choices=SERVICE_TYPE_CHOICES)
    zone = models.CharField(max_length=20, choices=ZONE_CHOICES)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=200.00,
                                     help_text="Base visiting/inspection charge")
    min_service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=300.00,
                                              help_text="Minimum service charge (excluding parts)")
    max_service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=1500.00,
                                              help_text="Maximum typical service charge")
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['service_type', 'zone']
        ordering = ['service_type', 'zone']
        verbose_name = 'Service Price'
        verbose_name_plural = 'Service Prices'
    
    def __str__(self):
        return f"{self.service_type} - {self.get_zone_display()}: ₹{self.base_price}"
    
    @classmethod
    def get_zone_for_area(cls, area):
        """Get the zone for a given area."""
        return cls.AREA_TO_ZONE.get(area, 'OTHER')
    
    @classmethod
    def get_price(cls, service_type, area):
        """
        Get pricing for a service type and area.
        Returns dict with base_price, min_service_charge, max_service_charge.
        """
        zone = cls.get_zone_for_area(area)
        try:
            price = cls.objects.get(service_type=service_type, zone=zone, is_active=True)
            return {
                'found': True,
                'base_price': float(price.base_price),
                'min_service_charge': float(price.min_service_charge),
                'max_service_charge': float(price.max_service_charge),
                'zone': zone,
                'zone_display': price.get_zone_display(),
            }
        except cls.DoesNotExist:
            # Return default pricing if not configured
            return {
                'found': False,
                'base_price': 200.00,
                'min_service_charge': 250.00,
                'max_service_charge': 700.00,
                'zone': zone,
                'zone_display': 'Default',
            }


# 6b. Appointment System
class Appointment(models.Model):
    SERVICE_CHOICES = [
        # Sorted Alphabetically (Other at end)
        ('AC Installation', 'AC Installation'),
        ('CCTV Installation', 'CCTV Installation'),
        ('Cooler Repair', 'Cooler Repair'),
        ('Electrical Wiring / Short Circuit', 'Electrical Wiring / Short Circuit'),
        ('Fan / Motor Repair', 'Fan / Motor Repair'),
        ('Fan Installation', 'Fan Installation'),
        ('Fridge Repair', 'Fridge Repair'),
        ('Geyser Installation', 'Geyser Installation'),
        ('Geyser Repair', 'Geyser Repair'),
        ('LED / Tube Light Repair', 'LED / Tube Light Repair'),
        ('TV Installation', 'TV Installation'),
        ('Underground Wiring', 'Underground Wiring'),
        ('Washing Machine Repair', 'Washing Machine Repair'),
        ('Other Appliance Repair', 'Other Appliance Repair'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('In Progress', 'In Progress'),
        ('Approved', 'Approved'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    CITY_CHOICES = [
        ('Indore', 'Indore'),
    ]

    AREA_CHOICES = [
        # Sorted Alphabetically (Other at end)
        ('Abhinandan Nagar', 'Abhinandan Nagar'),
        ('Annapurna Nagar', 'Annapurna Nagar'),
        ('Bapat Square', 'Bapat Square'),
        ('Chhatribagh', 'Chhatribagh'),
        ('Gauri Nagar', 'Gauri Nagar'),
        ('Gumasta Nagar', 'Gumasta Nagar'),
        ('Hawa Bangla', 'Hawa Bangla'),
        ('Juni Indore', 'Juni Indore'),
        ('Kanadia Road', 'Kanadia Road'),
        ('Kesar Bagh', 'Kesar Bagh'),
        ('LIG Colony', 'LIG Colony'),
        ('Luv Kush', 'Luv Kush'),
        ('Mahalaxmi Nagar', 'Mahalaxmi Nagar'),
        ('Malwa Mill', 'Malwa Mill'),
        ('Manik Bagh', 'Manik Bagh'),
        ('MR10', 'MR10'),
        ('Nipania', 'Nipania'),
        ('Palasia', 'Palasia'),
        ('Pardesipura', 'Pardesipura'),
        ('Patnipura', 'Patnipura'),
        ('Prime City', 'Prime City'),
        ('Rajendra Nagar', 'Rajendra Nagar'),
        ('Rajwada', 'Rajwada'),
        ('Royal Bungalow City', 'Royal Bungalow City'),
        ('Scheme No. 74', 'Scheme No. 74'),
        ('Silicon City', 'Silicon City'),
        ('Snehlataganj', 'Snehlataganj'),
        ('Sukhliya', 'Sukhliya'),
        ('Sundar Nagar', 'Sundar Nagar'),
        ('Tilak Nagar', 'Tilak Nagar'),
        ('Usha Nagar', 'Usha Nagar'),
        ('Veena Nagar', 'Veena Nagar'),
        ('Vijay Nagar', 'Vijay Nagar'),
        ('Yashwant Ganj', 'Yashwant Ganj'),
        ('Zanjeerwala Square', 'Zanjeerwala Square'),
        # Fallback option at end
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
    
    # New: Link to dynamic ServiceType (for new bookings)
    service = models.ForeignKey('ServiceType', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='appointments', help_text="Selected service from admin-managed list")
    # Legacy: Keep service_type for backward compatibility with existing data
    service_type = models.CharField(max_length=100, choices=SERVICE_CHOICES, blank=True, null=True)
    
    date = models.DateField()
    time = models.TimeField()
    problem_description = models.TextField()

    
    # Pricing (distance-based from ServiceType)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                       help_text="Distance from shop in KM")
    visiting_charge = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    extra_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pricing_confirmed = models.BooleanField(default=False, 
                                             help_text="True if price is confirmed by admin")
    
    # Assigned Electrician (for admin assignments)
    assigned_electrician = models.ForeignKey('Electrician', on_delete=models.SET_NULL,
                                              null=True, blank=True, related_name='appointments',
                                              help_text="Electrician assigned to this appointment")
    is_admin_booked = models.BooleanField(default=False, 
                                           help_text="True if appointment was booked by admin on behalf of customer")
    admin_notes = models.TextField(blank=True, null=True, 
                                    help_text="Internal notes for admin (not visible to customer)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    cancellation_reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        service_name = self.service_type or (self.service.name if self.service else 'Unknown')
        return f"{self.customer_name} - {service_name} ({self.date})"

    @property
    def total_charge(self):
        return self.visiting_charge + self.extra_charge
    
    @property
    def service_name(self):
        """Get service name from either the ForeignKey or the legacy CharField."""
        if self.service:
            return self.service.name
        return self.service_type or 'Unknown'
    
    def get_calculated_charge(self):
        """Get charge based on service and distance."""
        if self.service and self.distance_km:
            return self.service.get_charge_for_distance(float(self.distance_km))
        return (float(self.visiting_charge), True)

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
    shop_address = models.TextField(default="B-155,Abhinandan Nagar,Indore, MP")
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
                mrp=item.mrp,
                discount=item.discount,
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
    
    @property
    def total_discount(self):
        """Calculate total discount from all items"""
        total = sum(item.discount or 0 for item in self.items.all())
        return round(total, 2)
    
    @property
    def average_discount_percentage(self):
        """Calculate average discount percentage across all items"""
        items_with_mrp = [item for item in self.items.all() if item.mrp and item.mrp > 0]
        if not items_with_mrp:
            return 0
        avg_pct = sum(item.discount_percentage for item in items_with_mrp) / len(items_with_mrp)
        return round(avg_pct, 1)
    
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
    
    # Pricing fields
    mrp = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="MRP (Maximum Retail Price)",
        help_text="Original MRP of the product"
    )
    discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        null=True,
        blank=True,
        verbose_name="Discount Amount",
        help_text="Total discount applied (calculated from MRP - Unit Price)"
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Selling Price",
        help_text="Final selling price per unit after discount"
    )
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Item description/notes
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = "Receipt Item"
        verbose_name_plural = "Receipt Items"
    
    
    def __str__(self):
        return f"{self.item_name} x {self.quantity}"
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage from MRP"""
        if self.mrp and self.unit_price and self.mrp > 0:
            discount_pct = ((self.mrp - self.unit_price) / self.mrp) * 100
            return round(discount_pct, 1)
        return 0
    
    def save(self, *args, **kwargs):
        """Auto-calculate line total and discount"""
        # Calculate discount if MRP is provided
        if self.mrp and self.mrp > self.unit_price:
            self.discount = (self.mrp - self.unit_price) * self.quantity
        else:
            self.discount = 0.00
            
        # Calculate line total
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# 16. User Notifications System (TASK 2)
class Notification(models.Model):
    """
    Admin-created notifications that can be sent to specific users or groups.
    No email/push - only visible in user's notification section.
    """
    TARGET_CHOICES = [
        ('ALL', 'All Users'),
        ('LOCATION', 'By Location'),
        ('AREA', 'By Area'),
        ('INDIVIDUAL', 'Individual User'),
    ]
    
    title = models.CharField(max_length=200, help_text="Notification title/heading")
    message = models.TextField(help_text="Notification message content")
    image = models.ImageField(upload_to='notification_images/', blank=True, null=True, help_text="Optional notification image")
    
    # Targeting
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='ALL')
    target_city = models.CharField(max_length=100, blank=True, null=True, help_text="Target specific city")
    target_area = models.CharField(max_length=100, blank=True, null=True, help_text="Target specific area")
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True, 
        related_name='targeted_notifications',
        help_text="Specific users to target (for INDIVIDUAL type)"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, help_text="Whether this notification is active")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
    
    def __str__(self):
        return f"{self.title} ({self.target_type})"
    
    def get_target_users_queryset(self):
        """Get queryset of users this notification should be sent to"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if self.target_type == 'ALL':
            return User.objects.filter(role='USER')
        elif self.target_type == 'LOCATION':
            return User.objects.filter(role='USER', city=self.target_city)
        elif self.target_type == 'AREA':
            # Assuming area is stored in address_line1 or similar field
            return User.objects.filter(role='USER', address_line1__icontains=self.target_area)
        elif self.target_type == 'INDIVIDUAL':
            return self.target_users.all()
        return User.objects.none()


class UserNotification(models.Model):
    """
    Junction table linking notifications to specific users.
    Tracks read/unread status and allows deletion.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='user_notifications'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'notification')
        verbose_name = "User Notification"
        verbose_name_plural = "User Notifications"
    
    def __str__(self):
        return f"{self.notification.title} for {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class SiteAnnouncement(models.Model):
    """
    Site-wide announcements that appear as popups/toasts when users visit.
    Admin can control position, styling, and target audience.
    """
    POSITION_CHOICES = [
        ('center', 'Center Modal'),
        ('bottom_right', 'Bottom Right Toast'),
        ('both', 'Both Positions'),
    ]
    
    STYLE_CHOICES = [
        ('info', 'Info (Blue)'),
        ('success', 'Success (Green)'),
        ('warning', 'Warning (Yellow)'),
        ('danger', 'Danger (Red)'),
        ('primary', 'Primary (Brand)'),
    ]
    
    TARGET_CHOICES = [
        ('all', 'All Visitors'),
        ('logged_in', 'Logged In Users Only'),
        ('guests', 'Guests Only'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField(help_text="Main announcement message. HTML allowed.")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='bottom_right')
    style = models.CharField(max_length=20, choices=STYLE_CHOICES, default='info')
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    
    # Display options
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True, help_text="Can users dismiss this announcement?")
    show_once_per_session = models.BooleanField(default=True, 
                                                  help_text="Only show once per browser session")
    
    # Button options
    button_text = models.CharField(max_length=50, blank=True, null=True, 
                                    help_text="Optional action button text")
    button_url = models.URLField(blank=True, null=True, 
                                  help_text="URL for the action button")
    
    # Scheduling
    start_date = models.DateTimeField(null=True, blank=True, 
                                       help_text="When to start showing (leave blank for immediately)")
    end_date = models.DateTimeField(null=True, blank=True, 
                                     help_text="When to stop showing (leave blank for indefinitely)")
    
    # Tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Site Announcement"
        verbose_name_plural = "Site Announcements"
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.title} ({status})"
    
    @property
    def is_currently_active(self):
        """Check if announcement should be shown now based on schedule"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    @classmethod
    def get_active_announcements(cls, user=None):
        """Get all currently active announcements for a user"""
        now = timezone.now()
        
        # Base queryset: active and within date range
        qs = cls.objects.filter(is_active=True)
        qs = qs.filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        )
        qs = qs.filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        )
        
        # Filter by target audience
        if user and user.is_authenticated:
            qs = qs.exclude(target_audience='guests')
        else:
            qs = qs.exclude(target_audience='logged_in')
        
        return qs

# End of models.py


# 17. Electrician Management System
class Electrician(models.Model):
    """
    Manages electricians who can be assigned to appointments.
    Admin controls which electricians are visible to users on the home page.
    """
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    profile_picture = models.ImageField(upload_to='electrician_pics/', blank=True, null=True)
    specializations = models.TextField(blank=True, help_text="Comma-separated list of specializations")
    experience_years = models.PositiveIntegerField(default=0, help_text="Years of experience")
    
    # Visibility Control
    show_on_home_page = models.BooleanField(default=False, 
        help_text="If checked, electrician will be visible on home page under 'Our Electricians'")
    is_active = models.BooleanField(default=True, help_text="Is this electrician currently available")
    
    # Additional Info
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about this electrician")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Electrician'
        verbose_name_plural = 'Electricians'
    
    def __str__(self):
        return f"{self.name} ({self.phone_number})"
    
    @classmethod
    def get_visible_electricians(cls):
        """Get electricians that should appear on home page."""
        return cls.objects.filter(show_on_home_page=True, is_active=True)
    
    @classmethod
    def get_active_electricians(cls):
        """Get all active electricians for assignment dropdowns."""
        return cls.objects.filter(is_active=True)
    
    def get_specializations_list(self):
        """Returns list of specializations."""
        if self.specializations:
            return [s.strip() for s in self.specializations.split(',')]
        return []


# 18. Warranty Management System
class Warranty(models.Model):
    """
    Tracks product warranties for customers.
    Admin can add/manage warranties, users can view their warranties.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('VOIDED', 'Voided'),
    ]
    
    DURATION_UNIT_CHOICES = [
        ('MONTHS', 'Months'),
        ('YEARS', 'Years'),
    ]
    
    # Customer Info
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='warranties',
                                  help_text="Link to user account if exists")
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    
    # Product Info
    product_name = models.CharField(max_length=200)
    product_serial = models.CharField(max_length=100, blank=True, null=True,
                                       help_text="Product serial number or identifier")
    product_brand = models.CharField(max_length=100, blank=True, null=True)
    product_model = models.CharField(max_length=100, blank=True, null=True)
    product_image = models.ImageField(upload_to='warranty_products/', blank=True, null=True)
    
    # Warranty Period
    purchase_date = models.DateField()
    warranty_duration = models.PositiveIntegerField(default=12, help_text="Warranty duration value")
    warranty_unit = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, default='MONTHS')
    warranty_expiry_date = models.DateField(blank=True, null=True, help_text="Auto-calculated on save")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    void_reason = models.TextField(blank=True, null=True, help_text="Reason if warranty was voided")
    
    # Additional Info
    purchase_invoice = models.CharField(max_length=100, blank=True, null=True,
                                         help_text="Invoice/Bill number")
    notes = models.TextField(blank=True, null=True)
    
    # Admin tracking
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, related_name='created_warranties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Warranty'
        verbose_name_plural = 'Warranties'
        indexes = [
            models.Index(fields=['customer_email', 'status']),
            models.Index(fields=['warranty_expiry_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.product_name} - {self.customer_name} (Expires: {self.warranty_expiry_date})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate expiry date
        if self.purchase_date and self.warranty_duration:
            from dateutil.relativedelta import relativedelta
            if self.warranty_unit == 'MONTHS':
                self.warranty_expiry_date = self.purchase_date + relativedelta(months=self.warranty_duration)
            else:  # YEARS
                self.warranty_expiry_date = self.purchase_date + relativedelta(years=self.warranty_duration)
        
        # Auto-update status based on expiry
        if self.warranty_expiry_date and self.status != 'VOIDED':
            from django.utils import timezone
            if self.warranty_expiry_date < timezone.now().date():
                self.status = 'EXPIRED'
            else:
                self.status = 'ACTIVE'
        
        # Try to link to existing user by email
        if not self.customer and self.customer_email:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                self.customer = User.objects.get(email__iexact=self.customer_email)
            except User.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    @property
    def days_remaining(self):
        """Returns days until warranty expires, or negative if expired."""
        if self.warranty_expiry_date:
            from django.utils import timezone
            delta = self.warranty_expiry_date - timezone.now().date()
            return delta.days
        return 0
    
    @property
    def is_expired(self):
        """Check if warranty is expired."""
        return self.status == 'EXPIRED' or (self.warranty_expiry_date and self.days_remaining < 0)
    
    def void_warranty(self, reason, admin_user=None):
        """Mark warranty as voided."""
        self.status = 'VOIDED'
        self.void_reason = reason
        self.save()
    
    @classmethod
    def get_user_warranties(cls, user):
        """Get warranties for a specific user (by account or email)."""
        if user and user.is_authenticated:
            return cls.objects.filter(
                models.Q(customer=user) | models.Q(customer_email__iexact=user.email)
            ).distinct()
        return cls.objects.none()
    
    @classmethod
    def update_expired_warranties(cls):
        """Utility method to update status of expired warranties."""
        from django.utils import timezone
        today = timezone.now().date()
        cls.objects.filter(
            warranty_expiry_date__lt=today,
            status='ACTIVE'
        ).update(status='EXPIRED')
