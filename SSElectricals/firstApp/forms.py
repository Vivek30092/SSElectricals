from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Appointment, Product, Order, Review, DailySales, DailyExpenditure
from .validators import validate_indian_phone, validate_strong_password, validate_upi_id, validate_address_format, validate_pincode

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        validators=[validate_strong_password],
        help_text='Must be 8+ characters with uppercase, number, and symbol'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        help_text='Enter the same password for verification'
    )
    
    class Meta:
        model = CustomUser
        fields = ('phone_number', 'email', 'first_name', 'last_name', 'address')
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit mobile number',
                'pattern': '[0-9]{10}',
                'maxlength': '10'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'})
        }
        help_texts = {
            'phone_number': 'Enter 10-digit Indian mobile number',
            'email': 'We\'ll never share your email with anyone'
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone_number) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.phone_number  # Set username to phone number
        if commit:
            user.save()
        return user

class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'house_number', 'address_line1', 'city', 'landmark', 'pincode', 'profile_picture', 'theme_preference')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{10}',
                'maxlength': '10',
                'placeholder': 'Phone Number'
            }),
            'house_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House Number', 'autocomplete': 'off'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1', 'autocomplete': 'off'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City', 'autocomplete': 'off'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Near Landmark (Optional)', 'autocomplete': 'off'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode', 'autocomplete': 'off'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'theme_preference': forms.Select(attrs={'class': 'form-select'})
        }

class CheckoutForm(forms.Form):
    # Fulfillment Type - Pick from Store or Online Delivery
    fulfillment_type = forms.ChoiceField(
        choices=[
            ('DELIVERY', 'Online Delivery'),
            ('PICKUP', 'Pick from Store'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'fulfillment-type-radio', 'id': 'id_fulfillment_type'}),
        initial='DELIVERY',
        label='How would you like to receive your order?'
    )
    
    house_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House Number', 'id': 'id_house_number'}),
        label='House Number',
        required=False  # Optional for pickup orders
    )
    address_line1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1 (Street/Road)', 'id': 'id_address_line1'}),
        label='Address Line 1',
        required=False  # Optional for pickup orders
    )
    address_line2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2 (Optional)', 'id': 'id_address_line2'}),
        label='Address Line 2'
    )
    pincode = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode', 'id': 'id_pincode'}),
        validators=[validate_pincode],
        label='Pincode',
        required=False  # Optional for pickup orders
    )
    city = forms.CharField(
        initial='Indore',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'value': 'Indore', 'id': 'id_city'}),
        required=False
    )
    area = forms.ChoiceField(
        choices=Appointment.AREA_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_area', 'onchange': 'toggleOtherArea(this)'}),
        label='Area',
        required=False  # Optional for pickup orders
    )
    other_area = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your area name', 'id': 'id_other_area', 'style': 'display:none;'})
    )
    landmark = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Near Landmark', 'id': 'id_landmark'}),
        label='Nearby Landmark'
    )

    payment_method = forms.ChoiceField(
        choices=[
            ('COD', 'Cash on Delivery (COD)'),
            ('Online_QR', 'Online (Pay at delivery using QR code)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'payment-method-radio'}),
        initial='COD',
        help_text='Select your preferred payment method'
    )
    
    upi_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'yourname@paytm',
            'id': 'upi-id-input'
        }),
        validators=[validate_upi_id],
        help_text='Enter UPI ID (e.g., user@paytm, user@gpay)'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        upi_id = cleaned_data.get('upi_id')
        fulfillment_type = cleaned_data.get('fulfillment_type')
        
        # For DELIVERY orders, validate address fields
        if fulfillment_type == 'DELIVERY':
            house_number = cleaned_data.get('house_number')
            address_line1 = cleaned_data.get('address_line1')
            pincode = cleaned_data.get('pincode')
            
            if not house_number:
                self.add_error('house_number', 'House number is required for delivery orders.')
            if not address_line1:
                self.add_error('address_line1', 'Address is required for delivery orders.')
            if not pincode:
                self.add_error('pincode', 'Pincode is required for delivery orders.')
            
            # Handle "Other" area
            area = cleaned_data.get('area')
            other_area = cleaned_data.get('other_area')

            if area == 'Other':
                if not other_area:
                    self.add_error('other_area', 'Please specify your area.')
                else:
                    cleaned_data['area'] = other_area
        
        # For PICKUP orders, address is not required
        # Just pass through without validation
        
        # Validate UPI ID if UPI payment is selected
        if payment_method == 'UPI':
            if not upi_id:
                raise forms.ValidationError('UPI ID is required for UPI payment.')
            # Additional UPI validation happens via validator
        
        return cleaned_data

class AppointmentForm(forms.ModelForm):
    other_area = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your area name', 'id': 'id_other_area', 'style': 'display:none;'}))
    
    # New: Dynamic service selection from database
    service = forms.ModelChoiceField(
        queryset=None,  # Set dynamically in __init__
        empty_label="-- Select a Service --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_service'}),
        required=True,
        help_text="Select the service you need"
    )

    class Meta:
        model = Appointment
        fields = ['customer_name', 'phone', 'email', 'pincode', 'house_number', 'address_line1', 'address_line2', 'landmark', 'city', 'area', 'service', 'date', 'time', 'problem_description', 'visiting_charge', 'distance_km']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode', 'id': 'id_pincode'}),
            'house_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House Number', 'id': 'id_house_number'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1', 'id': 'id_address_line1'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2', 'id': 'id_address_line2'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Near Landmark (Optional)', 'id': 'id_landmark'}),
            'city': forms.Select(attrs={'class': 'form-select', 'readonly': 'readonly'}),
            'area': forms.Select(choices=Appointment.AREA_CHOICES, attrs={'class': 'form-select', 'id': 'id_area', 'onchange': 'toggleOtherArea(this)'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'min': '09:00', 'max': '20:00'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the issue...'}),
            'visiting_charge': forms.HiddenInput(),
            'distance_km': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force city to be Indore and readonly-ish
        self.fields['city'].initial = 'Indore'
        self.fields['landmark'].required = False
        # Add validators
        self.fields['phone'].validators.append(validate_indian_phone)
        self.fields['city'].disabled = True 
        # Manually set choices for area since we removed them from model
        self.fields['area'].widget.choices = Appointment.AREA_CHOICES
        
        # Dynamic service selection - only show active services
        from .models import ServiceType
        self.fields['service'].queryset = ServiceType.objects.filter(is_active=True).order_by('display_order', 'name')

    def clean_city(self):
        return 'Indore'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        validate_indian_phone(phone)
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        pincode_str = str(pincode) if pincode else ''
        if pincode and not (pincode_str.startswith('452') or pincode_str.startswith('453')):
            raise forms.ValidationError("Service is available only in Indore (Pincode starting with 452 or 453).")
        return pincode

    def clean(self):
        cleaned_data = super().clean()
        area = cleaned_data.get('area')
        other_area = cleaned_data.get('other_area')

        if area == 'Other':
            if not other_area:
                self.add_error('other_area', 'Please specify your area.')
            else:
                cleaned_data['area'] = other_area
        
        # Calculate visiting charge based on service and distance
        service = cleaned_data.get('service')
        distance_km = cleaned_data.get('distance_km')
        
        if service:
            charge, is_confirmed = service.get_charge_for_distance(float(distance_km) if distance_km else None)
            if charge:
                cleaned_data['visiting_charge'] = charge
            cleaned_data['pricing_confirmed'] = is_confirmed
        
        return cleaned_data


class AdminAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['customer_name', 'phone', 'email', 'address', 'city', 'service_type', 'date', 'time', 'problem_description', 'visiting_charge', 'extra_charge', 'status']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'visiting_charge': forms.NumberInput(attrs={'class': 'form-control'}),
            'extra_charge': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class EmailSignupForm(forms.Form):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    phone = forms.CharField(max_length=10, validators=[validate_indian_phone], widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Phone Number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}))
    pincode = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'id': 'id_password'}), validators=[validate_strong_password])
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password', 'id': 'id_confirm_password'}))
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("Phone number is already registered.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

class AccountDeletionForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password to confirm'}), label="Confirm Password")

class EmailLoginForm(forms.Form):
    identifier = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email or phone number'}))

    def clean_identifier(self):
        identifier = self.cleaned_data.get('identifier')
        if not identifier:
            raise forms.ValidationError("This field is required.")
        
        # Check if it's an email
        if '@' in identifier:
            if not CustomUser.objects.filter(email=identifier).exists():
                raise forms.ValidationError("No account found with this email.")
        # Check if it's a phone number
        elif identifier.isdigit() and len(identifier) == 10:
             if not CustomUser.objects.filter(phone_number=identifier).exists():
                raise forms.ValidationError("No account found with this phone number.")
        else:
             raise forms.ValidationError("Enter a valid email or 10-digit phone number.")
             
        return identifier

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 6-digit OTP', 'style': 'text-align: center; letter-spacing: 5px;'}))

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found with this email.")
        return email

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'}), validators=[validate_strong_password])
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm New Password'}))

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your Message'}))

class CancelAppointmentForm(forms.Form):
    REASON_CHOICES = [
        ('Changed my mind', 'Changed my mind'),
        ('Found another service', 'Found another service'),
        ('Scheduling conflict', 'Scheduling conflict'),
        ('Service no longer needed', 'Service no longer needed'),
        ('Other', 'Other'),
    ]
    reason = forms.ChoiceField(choices=REASON_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    other_reason = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please specify if other...'}))

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'short_description', 'description', 'price', 'discount_price', 'stock_quantity', 'brand', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control', 
                'maxlength': '200',
                'placeholder': 'Brief summary for product cards (max 200 characters)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 6,
                'placeholder': 'Detailed description (HTML supported)'
            }),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'short_description': 'Short Description (Plain Text)',
            'description': 'Long Description (HTML Enabled)',
            'stock_quantity': 'Stock Quantity (For Admin Only)',
        }
class CancelOrderForm(forms.ModelForm):
    reason_choices = [
        ('Changed my mind', 'Changed my mind'),
        ('Found a better price', 'Found a better price'),
        ('Ordered by mistake', 'Ordered by mistake'),
        ('Delivery time too long', 'Delivery time too long'),
        ('Other', 'Other'),
    ]
    reason_select = forms.ChoiceField(choices=reason_choices, widget=forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleOtherReason(this)'}), label="Reason for Cancellation")
    other_reason = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please specify details...', 'style': 'display:none;'}))

    class Meta:
        model = Order
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        reason_select = cleaned_data.get('reason_select')
        other_reason = cleaned_data.get('other_reason')

        if reason_select == 'Other':
            if not other_reason:
                self.add_error('other_reason', 'Please specify the reason.')
            else:
                 cleaned_data['final_reason'] = other_reason
        else:
            cleaned_data['final_reason'] = reason_select
        
        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'image']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your review here...'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'image': 'Upload Photo (Optional)'
        }
        help_texts = {
            'image': 'Share a photo of the product (Max 5MB, JPG/PNG)'
        }

class DailySalesForm(forms.ModelForm):
    class Meta:
        model = DailySales
        fields = ['date', 'total_sales', 'online_received', 'cash_received', 'labor_charge', 'delivery_charge', 'subtotal', 'remark', 'other_remark']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_sales': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
                'id': 'id_total_sales'
            }),
            'online_received': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
                'id': 'id_online_received'
            }),
            # Cash is READ-ONLY - Auto-calculated as Total Sales - Online
            'cash_received': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
                'id': 'id_cash_received',
                'readonly': 'readonly',
                'style': 'background-color: #e9ecef; cursor: not-allowed;'
            }),
            'labor_charge': forms.NumberInput(attrs={
                'class': 'form-control smart-default-field', 
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
                'data-default': '0'
            }),
            'delivery_charge': forms.NumberInput(attrs={
                'class': 'form-control smart-default-field',
                'placeholder': '0', 
                'step': '0.01',
                'min': '0',
                'data-default': '0'
            }),
            # Subtotal is READ-ONLY - Auto-calculated as Total Sales
            'subtotal': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
                'id': 'id_subtotal',
                'readonly': 'readonly',
                'style': 'background-color: #e9ecef; cursor: not-allowed;'
            }),
            'remark': forms.Select(attrs={'class': 'form-select', 'onchange': 'if(this.value=="Other"){document.getElementById("id_other_remark").parentElement.style.display="block";}else{document.getElementById("id_other_remark").parentElement.style.display="none";}'}),
            'other_remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        help_texts = {
            'total_sales': 'Enter the total sales amount for the day',
            'online_received': 'Enter online payment received (default: 0)',
            'cash_received': 'Auto-calculated: Total Sales − Online Received',
            'labor_charge': 'Optional – enter only if applicable',
            'delivery_charge': 'Optional – enter only if applicable',
            'subtotal': 'Auto-calculated: equals Total Sales',
        }
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        # Check if entry already exists for this date (excluding current instance when editing)
        existing = DailySales.objects.filter(date=date)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError(
                f"⚠️ Data for {date.strftime('%B %d, %Y')} already exists. "
                f"Please edit the existing entry instead of creating a new one."
            )
        return date
    
    def clean(self):
        cleaned_data = super().clean()
        total_sales = cleaned_data.get('total_sales')
        online_received = cleaned_data.get('online_received')
        
        # Convert None to 0 for calculation
        total_sales = total_sales or 0
        online_received = online_received or 0
        
        # VALIDATION: Online received cannot exceed Total Sales
        if online_received > total_sales:
            raise forms.ValidationError(
                f"⚠️ Invalid Amount: Online Received (₹{online_received}) cannot exceed "
                f"Total Sales (₹{total_sales}). Please correct the values."
            )
        
        # AUTO-CALCULATE: Cash Received = Total Sales - Online Received
        calculated_cash = total_sales - online_received
        cleaned_data['cash_received'] = calculated_cash
        
        # AUTO-CALCULATE: Subtotal = Total Sales (Online + Cash)
        cleaned_data['subtotal'] = total_sales
        
        return cleaned_data


class DailyExpenditureForm(forms.ModelForm):
    class Meta:
        model = DailyExpenditure
        fields = ['date', 'online_amount', 'cash_amount', 'total', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'online_amount': forms.NumberInput(attrs={
                'class': 'form-control smart-default-field',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
                'data-default': '0'
            }),
            'cash_amount': forms.NumberInput(attrs={
                'class': 'form-control smart-default-field',
                'placeholder': '0',
                'step': '0.01',
                'min': '0',
                'data-default': '0'
            }),
            'total': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'style': 'background-color: #e9ecef;'
            }),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        help_texts = {
            'online_amount': 'Online expenses for the day',
            'cash_amount': 'Cash expenses for the day',
            'total': 'Auto-calculated (Online + Cash)',
        }
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        # Check if entry already exists for this date (excluding current instance when editing)
        existing = DailyExpenditure.objects.filter(date=date)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError(
                f"⚠️ Expense data for {date.strftime('%B %d, %Y')} already exists. "
                f"Please edit the existing entry instead of creating a new one."
            )
        return date
