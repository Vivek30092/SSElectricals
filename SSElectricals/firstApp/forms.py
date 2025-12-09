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
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'house_number', 'address_line1', 'city', 'landmark', 'pincode', 'profile_picture')
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
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'})
        }

class CheckoutForm(forms.Form):
    house_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'House Number'}),
        label='House Number'
    )
    address_line1 = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1 (Area/Colony)'}),
        label='Address Line 1'
    )
    address_line2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2 (Optional)'}),
        label='Address Line 2'
    )
    pincode = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
        validators=[validate_pincode], # Updated validator
        label='Pincode'
    )
    city = forms.CharField(
        initial='Indore',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'value': 'Indore'}),
        required=False
    )

    payment_method = forms.ChoiceField(
        choices=[
            ('COD', 'Cash on Delivery (COD) Only'),
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
        
        # Validate UPI ID if UPI payment is selected
        if payment_method == 'UPI':
            if not upi_id:
                raise forms.ValidationError('UPI ID is required for UPI payment.')
            # Additional UPI validation happens via validator
        
        return cleaned_data

class AppointmentForm(forms.ModelForm):
    other_area = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your area name', 'id': 'id_other_area', 'style': 'display:none;'}))

    class Meta:
        model = Appointment
        fields = ['customer_name', 'phone', 'email', 'pincode', 'house_number', 'address_line1', 'address_line2', 'landmark', 'city', 'area', 'service_type', 'date', 'time', 'problem_description', 'visiting_charge']
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
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'min': '09:00', 'max': '20:00'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the issue...'}),
            'visiting_charge': forms.HiddenInput(),
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

    def clean_city(self):
        return 'Indore'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        validate_indian_phone(phone)
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode and not str(pincode).startswith('452'):
            raise forms.ValidationError("Service is available only in Indore (Pincode starting with 452).")
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
        fields = ['name', 'category', 'description', 'price', 'discount_price', 'stock_quantity', 'brand', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
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
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your review here...'}),
        }

class DailySalesForm(forms.ModelForm):
    class Meta:
        model = DailySales
        fields = ['date', 'total_sales', 'online_received', 'cash_received', 'subtotal', 'remark', 'other_remark']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_sales': forms.NumberInput(attrs={'class': 'form-control'}),
            'online_received': forms.NumberInput(attrs={'class': 'form-control'}),
            'cash_received': forms.NumberInput(attrs={'class': 'form-control'}),
            'subtotal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave empty to auto-calculate'}),
            'remark': forms.Select(attrs={'class': 'form-select', 'onchange': 'if(this.value=="Other"){document.getElementById("id_other_remark").parentElement.style.display="block";}else{document.getElementById("id_other_remark").parentElement.style.display="none";}'}),
            'other_remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class DailyExpenditureForm(forms.ModelForm):
    class Meta:
        model = DailyExpenditure
        fields = ['date', 'amount', 'payment_method', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
