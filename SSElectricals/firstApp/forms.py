from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Appointment
from .validators import validate_indian_phone, validate_strong_password, validate_upi_id, validate_address_format

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
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'address', 'pincode', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '[0-9]{10}',
                'maxlength': '10'
            }),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'})
        }

class CheckoutForm(forms.Form):
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Enter your complete delivery address',
            'id': 'checkout-address'
        }),
        validators=[validate_address_format],
        help_text='Please provide your complete delivery address with pincode'
    )
    
    payment_method = forms.ChoiceField(
        choices=[
            ('COD', 'Cash on Delivery'),
            ('UPI', 'UPI Payment'),
            ('Card', 'Credit/Debit Card')
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
    class Meta:
        model = Appointment
        fields = ['customer_name', 'phone', 'email', 'address', 'city', 'service_type', 'date', 'time', 'problem_description']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Complete Address'}),
            'city': forms.Select(attrs={'class': 'form-select', 'readonly': 'readonly'}),
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time', 'min': '09:00', 'max': '20:00'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the issue...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force city to be Indore and readonly-ish (HTML readonly doesn't stop submission, but choice limits it)
        self.fields['city'].initial = 'Indore'
        # Add validators
        self.fields['phone'].validators.append(validate_indian_phone)
        self.fields['city'].disabled = True # This makes it read-only in Django form logic

    def clean_city(self):
        # Even if disabled, we want to ensure it's Indore
        return 'Indore'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        validate_indian_phone(phone)
        return phone

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
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found with this email.")
        return email

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


