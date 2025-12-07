from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Appointment, EmailOTP, CustomUser
from .forms import CustomUserCreationForm, CustomUserUpdateForm, CheckoutForm, AppointmentForm, EmailSignupForm, EmailLoginForm, OTPVerificationForm, AccountDeletionForm, ForgotPasswordForm, ResetPasswordForm
from .utils import send_otp_email, calculate_distance_and_price
import requests
from django.conf import settings

@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('product_list')

    # Initial estimates
    delivery_charge = 0 # Will be calculated on POST
    total_amount = cart.total_price 
    dist_km = 0

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            payment_method = 'COD' # Fixed as per requirement
            
            # Check stock availability
            for item in cart.items.all():
                if item.product.stock_quantity < item.quantity:
                    messages.error(request, f"{item.product.name} is out of stock or insufficient quantity available.")
                    return redirect('view_cart')
            
            # Calculate Delivery Charge
            dist_km, delivery_charge, error_msg = calculate_distance_and_price(address)
            
            if error_msg:
                messages.error(request, f"Delivery Error: {error_msg}")
                return render(request, 'firstApp/checkout.html', {
                    'form': form, 
                    'cart': cart, 
                    'delivery_charge': 0, 
                    'total_amount': cart.total_price
                })
            
            total_amount = cart.total_price + delivery_charge

            # Create Order
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=cart.total_price, # Base product price
                delivery_charge=delivery_charge,
                distance_km=dist_km,
                final_price=None, # To be confirmed by Admin
                status='Pending',
                payment_method=payment_method
            )
            
            # Create Order Items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.final_price
                )
                # Reduce Stock
                item.product.stock_quantity -= item.quantity
                item.product.save()
            
            # Clear Cart
            cart.items.all().delete()
            
            messages.success(request, f"Order placed successfully! Delivery distance: {dist_km} KM. Admin will contact you for final confirmation.")
            return redirect('order_history')
    else:
        # Pre-fill address from user profile
        initial_data = {}
        if request.user.house_number:
             full_address = f"{request.user.house_number}, {request.user.address_line1}, {request.user.city} - {request.user.pincode}"
             initial_data['address'] = full_address
        else:
             initial_data['address'] = request.user.address

        form = CheckoutForm(initial=initial_data)
        
    return render(request, 'firstApp/checkout.html', {
        'form': form, 
        'cart': cart, 
        'delivery_charge': "Calculated at checkout", 
        'total_amount': "Calculated at checkout"
    })

@login_required
def confirm_delivery_otp(request):
    """View for delivery person to enter OTP for an order."""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        otp = request.POST.get('otp')
        
        try:
            order = Order.objects.get(id=order_id, status='Out for Delivery')
            if order.delivery_otp and order.delivery_otp == otp.strip():
                order.status = 'Delivered'
                order.save()
                messages.success(request, f"Order #{order_id} marked as Delivered.")
            else:
                messages.error(request, "Invalid OTP or Order not ready for delivery.")
        except Order.DoesNotExist:
            messages.error(request, "Order not found or invalid status.")
            
    return render(request, 'firstApp/delivery_confirmation.html')

def home(request):
    categories = Category.objects.all()
    # Trending products could be random or latest
    trending_products = Product.objects.all().order_by('-created_at')[:8]
    return render(request, 'firstApp/home.html', {'categories': categories, 'trending_products': trending_products})

def product_list(request):
    products = Product.objects.all()
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    sort_by = request.GET.get('sort')
    
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    
    if category_id:
        products = products.filter(category_id=category_id)
        
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
        
    categories = Category.objects.all()
    return render(request, 'firstApp/product_list.html', {'products': products, 'categories': categories})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'firstApp/product_detail.html', {'product': product})

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'firstApp/signup.html', {'form': form})

@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        if 'delete_account' in request.POST:
            delete_form = AccountDeletionForm(request.POST)
            if delete_form.is_valid():
                password = delete_form.cleaned_data['password']
                if user.check_password(password):
                    user.delete()
                    messages.success(request, "Your account has been deleted.")
                    return redirect('home')
                else:
                    messages.error(request, "Incorrect password.")
            else:
                 messages.error(request, "Please enter your password to confirm deletion.")
            form = CustomUserUpdateForm(instance=user) # Re-init form to avoid unbound error in template
        else:
            form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                # Prevent email change if verified
                if user.is_email_verified and 'email' in form.changed_data:
                    messages.error(request, "Email cannot be changed after verification.")
                else:
                    form.save()
                    messages.success(request, "Profile updated successfully!")
                    return redirect('profile')
            delete_form = AccountDeletionForm()
    else:
        form = CustomUserUpdateForm(instance=user)
        if user.is_email_verified:
            form.fields['email'].widget.attrs['readonly'] = True
            form.fields['email'].help_text = "Email is verified and cannot be changed."
        delete_form = AccountDeletionForm()
        
    return render(request, 'firstApp/profile.html', {'form': form, 'delete_form': delete_form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{product.name} added to cart.")
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'firstApp/cart.html', {'cart': cart})

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
    return redirect('view_cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('view_cart')



@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'firstApp/orders.html', {'orders': orders})

def about(request):
    reviews = fetch_google_reviews()
    return render(request, 'firstApp/about.html', {'reviews': reviews})

from .forms import CustomUserCreationForm, CustomUserUpdateForm, CheckoutForm, AppointmentForm, EmailSignupForm, EmailLoginForm, OTPVerificationForm, AccountDeletionForm, ForgotPasswordForm, ResetPasswordForm, ContactForm, CancelAppointmentForm

# ... (rest of imports)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']
            
            # Send Email to Admin
            try:
                send_mail(
                    subject=f"New Contact Inquiry from {name}",
                    message=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['shivshaktielectrical1430@gmail.com'],
                    fail_silently=False,
                )
                messages.success(request, "Your message has been sent successfully!")
                return redirect('contact')
            except Exception as e:
                print(f"Contact Email Error: {e}")
                messages.error(request, "Failed to send message. Please try again later.")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'name': request.user.first_name + ' ' + request.user.last_name if request.user.first_name else request.user.username,
                'email': request.user.email
            }
        form = ContactForm(initial=initial_data)
        
    return render(request, 'firstApp/contact.html', {'form': form})

# Appointment Views
@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            if request.user.is_authenticated:
                appointment.user = request.user
                # If verified, force the email to be the user's email
                if request.user.is_email_verified:
                    appointment.email = request.user.email
            try:
                appointment.save()
                
                # Store ID for success page
                request.session['booked_appointment_id'] = appointment.id

                # --- Notification Logic ---
                try:
                    # 1. Collect Details
                    details = f"""
New Service Request Received

Full Name: {appointment.customer_name}
Mobile Number: {appointment.phone}
Email: {appointment.email if appointment.email else 'Not Provided'}
Address: {appointment.house_number}, {appointment.address_line1}, {appointment.address_line2 if appointment.address_line2 else ''}, {appointment.landmark if appointment.landmark else ''}, {appointment.city} - {appointment.pincode}
Service Type: {appointment.get_service_type_display()}
Date: {appointment.date}
Time: {appointment.time}
Description: {appointment.problem_description}
Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

Regards,
Shiv Shakti Electrical
"""
                    
                    # 2. Send Email to Admin
                    send_mail(
                        subject="New Service Request Received – Shiv Shakti Electrical",
                        message=details,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=['shivshaktielectrical1430@gmail.com'],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Notification Error: {e}")
                    # Log error but don't stop the user flow
                
                messages.success(request, "Your service request has been submitted successfully. Our team will contact you soon.")
                return redirect('appointment_success')
            except Exception as e:
                print(f"Appointment Save Error: {e}")
                messages.error(request, "Your request could not be processed. We will contact you soon.")
                return redirect('book_appointment')
        else:
            # Debugging: Print errors to console and show user
            print("Form Errors:", form.errors)
            messages.error(request, "Please correct the errors in the form.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'customer_name': request.user.first_name + ' ' + request.user.last_name if request.user.first_name else request.user.username,
                'phone': request.user.phone_number,
                'email': request.user.email,
                'house_number': request.user.house_number,
                'address_line1': request.user.address_line1 if request.user.address_line1 else request.user.address, # Fallback to old address field
                'city': request.user.city if request.user.city else 'Indore',
                'landmark': request.user.landmark,
                'pincode': request.user.pincode,
            }
        form = AppointmentForm(initial=initial_data)
        if request.user.is_authenticated:
            if request.user.is_email_verified:
                form.fields['email'].widget.attrs['readonly'] = True
                form.fields['email'].help_text = "Email is verified and cannot be changed."
            if request.user.pincode:
                form.fields['pincode'].widget.attrs['readonly'] = True
                form.fields['pincode'].help_text = "Pincode from your profile."
            if request.user.address_line1 or request.user.address:
                form.fields['address_line1'].widget.attrs['readonly'] = True
                form.fields['address_line1'].help_text = "Address from your profile."
            if request.user.house_number:
                form.fields['house_number'].widget.attrs['readonly'] = True
            if request.user.city:
                 # City is already readonly and set to Indore in form __init__, but we can ensure it matches
                 pass 
            if request.user.landmark:
                form.fields['landmark'].widget.attrs['readonly'] = True
    
    return render(request, 'firstApp/book_appointment.html', {'form': form})

def appointment_success(request):
    appointment_id = request.session.get('booked_appointment_id')
    appointment = None
    if appointment_id:
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            pass
            
    return render(request, 'firstApp/appointment_success.html', {'appointment': appointment})

@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'firstApp/my_appointments.html', {'appointments': appointments})

@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, user=request.user)
    
    if appointment.status == 'Cancelled':
        messages.warning(request, "This appointment is already cancelled.")
        return redirect('my_appointments')

    if request.method == 'POST':
        form = CancelAppointmentForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            other_reason = form.cleaned_data['other_reason']
            final_reason = f"{reason}: {other_reason}" if reason == 'Other' and other_reason else reason
            
            appointment.status = 'Cancelled'
            appointment.cancellation_reason = final_reason
            appointment.save()
            
            # Send Email to Admin
            try:
                send_mail(
                    subject=f"Service Cancellation - {appointment.customer_name}",
                    message=f"Appointment ID: {appointment.id}\nCustomer: {appointment.customer_name}\nReason: {final_reason}\nDate: {appointment.date}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['shivshaktielectrical1430@gmail.com'],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Cancellation Email Error: {e}")

            messages.success(request, "Appointment cancelled successfully.")
            return redirect('my_appointments')
    
    return redirect('my_appointments')


# AJAX API Endpoints
@login_required
def ajax_add_to_cart(request):
    """AJAX endpoint to add product to cart."""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        try:
            product = Product.objects.get(pk=product_id)
            
            # Check stock
            if product.stock_quantity < 1:
                return JsonResponse({'success': False, 'message': 'Product out of stock'})
            
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
            
            if not item_created:
                if cart_item.quantity >= product.stock_quantity:
                    return JsonResponse({'success': False, 'message': 'Maximum stock reached'})
                cart_item.quantity += 1
                cart_item.save()
            
            cart_count = cart.items.count()
            return JsonResponse({'success': True, 'cart_count': cart_count})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def ajax_update_cart(request):
    """AJAX endpoint to update cart item quantity."""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        try:
            cart_item = CartItem.objects.get(pk=item_id, cart__user=request.user)
            
            if quantity > 0:
                if quantity > cart_item.product.stock_quantity:
                    return JsonResponse({'success': False, 'message': 'Insufficient stock'})
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
            
            cart = cart_item.cart
            cart_count = cart.items.count()
            cart_total = cart.total_price
            item_total = cart_item.total_price if quantity > 0 else 0
            
            return JsonResponse({
                'success': True,
                'cart_count': cart_count,
                'cart_total': float(cart_total),
                'item_total': float(item_total)
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def ajax_search(request):
    """AJAX endpoint for search suggestions."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({ 'results': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:5]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.final_price),
            'image': product.image.url if product.image else ''
        })
    
    return JsonResponse({'results': results})



def email_signup(request):
    if request.method == 'POST':
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Generate OTP
            otp = EmailOTP.generate_otp()
            # Save OTP
            EmailOTP.objects.create(email=email, otp=otp)
            # Send Email
            if send_otp_email(email, otp):
                # Store signup data in session
                request.session['signup_data'] = form.cleaned_data
                request.session['otp_email'] = email
                request.session['otp_purpose'] = 'signup'
                messages.success(request, f"OTP sent to {email}")
                return redirect('email_signup_verify')
            else:
                messages.error(request, "Failed to send OTP. Please try again.")
    else:
        form = EmailSignupForm()
    return render(request, 'firstApp/signup_email.html', {'form': form})

def email_signup_verify(request):
    email = request.session.get('otp_email')
    if not email:
        messages.error(request, "Session expired.")
        return redirect('email_signup')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data['otp']
            # Verify OTP
            try:
                otp_obj = EmailOTP.objects.filter(email=email).latest('created_at')
                success, message = otp_obj.verify(otp_entered)
                if success:
                    # Create User
                    data = request.session.get('signup_data')
                    user = CustomUser.objects.create_user(
                        username=data['phone'], # Using phone as username per model
                        email=data['email'],
                        phone_number=data['phone'],
                        password=data['password'],
                        first_name=data['full_name'].split(' ')[0],
                        last_name=' '.join(data['full_name'].split(' ')[1:]) if ' ' in data['full_name'] else '',
                        address=data.get('address', ''),
                        pincode=data.get('pincode', '')
                    )
                    user.is_email_verified = True
                    user.save()
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    # Cleanup
                    del request.session['signup_data']
                    del request.session['otp_email']
                    del request.session['otp_purpose']
                    messages.success(request, "Signup successful!")
                    return redirect('home')
                else:
                    messages.error(request, message)
            except EmailOTP.DoesNotExist:
                messages.error(request, "Invalid OTP request.")
    else:
        form = OTPVerificationForm()
    return render(request, 'firstApp/signup_otp_verify.html', {'form': form, 'email': email})

def email_login(request):
    if request.method == 'POST':
        login_type = request.POST.get('login_type')
        
        if login_type == 'password':
            identifier = request.POST.get('identifier')
            password = request.POST.get('password')
            
            if not identifier or not password:
                messages.error(request, "Please enter both identifier and password.")
            else:
                try:
                    # Determine if identifier is email or phone
                    if '@' in identifier:
                        user_obj = CustomUser.objects.get(email=identifier)
                    else:
                        user_obj = CustomUser.objects.get(phone_number=identifier)
                        
                    user = authenticate(request, username=user_obj.phone_number, password=password)
                    if user:
                        login(request, user)
                        messages.success(request, "Login successful!")
                        return redirect('home')
                    else:
                        messages.error(request, "Invalid credentials.")
                except CustomUser.DoesNotExist:
                    messages.error(request, "No account found.")
            form = EmailLoginForm(initial={'identifier': identifier}) 
            
        elif login_type == 'otp':
            # OTP login currently only supports email as per previous implementation, 
            # but we can extend it if needed. For now, let's keep it email-based or update form.
            # The user request specifically mentioned "Enable login using either email or phone number".
            # Assuming this applies to password login primarily. 
            # If OTP login is also needed for phone, we'd need SMS integration.
            # Let's stick to email for OTP for now as per existing code, or update if requested.
            # Actually, let's update the form usage here too.
            form = EmailLoginForm(request.POST)
            if form.is_valid():
                identifier = form.cleaned_data['identifier']
                
                if '@' in identifier:
                     email = identifier
                else:
                     # If phone, we need to find the email associated to send OTP (since we only have email OTP)
                     try:
                         user = CustomUser.objects.get(phone_number=identifier)
                         email = user.email
                     except CustomUser.DoesNotExist:
                         messages.error(request, "User not found.")
                         return render(request, 'firstApp/login_email.html', {'form': form})

                otp = EmailOTP.generate_otp()
                EmailOTP.objects.create(email=email, otp=otp)
                if send_otp_email(email, otp):
                    request.session['otp_email'] = email
                    request.session['otp_purpose'] = 'login'
                    messages.success(request, f"OTP sent to {email}")
                    return redirect('email_login_verify')
                else:
                    messages.error(request, "Failed to send OTP.")
        else:
             messages.error(request, "Invalid login method.")
             form = EmailLoginForm()
    else:
        form = EmailLoginForm()
    return render(request, 'firstApp/login_email.html', {'form': form})

def email_login_verify(request):
    email = request.session.get('otp_email')
    if not email:
        messages.error(request, "Session expired.")
        return redirect('email_login')
        
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data['otp']
            try:
                otp_obj = EmailOTP.objects.filter(email=email).latest('created_at')
                success, message = otp_obj.verify(otp_entered)
                if success:
                    try:
                        user = CustomUser.objects.get(email=email)
                        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                        del request.session['otp_email']
                        del request.session['otp_purpose']
                        messages.success(request, "Login successful!")
                        return redirect('home')
                    except CustomUser.DoesNotExist:
                        messages.error(request, "User account not found.")
                    except CustomUser.MultipleObjectsReturned:
                        messages.error(request, "Multiple accounts found with this email. Please contact support.")
                    except Exception as e:
                        messages.error(request, f"Login failed: {str(e)}")
                else:
                    messages.error(request, message)
            except EmailOTP.DoesNotExist:
                messages.error(request, "Invalid OTP request.")
    else:
        form = OTPVerificationForm()
    return render(request, 'firstApp/login_email_otp_verify.html', {'form': form, 'email': email})


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = EmailOTP.generate_otp()
            EmailOTP.objects.create(email=email, otp=otp)
            if send_otp_email(email, otp):
                request.session['otp_email'] = email
                request.session['otp_purpose'] = 'reset_password'
                messages.success(request, f"OTP sent to {email}")
                return redirect('forgot_password_verify')
            else:
                messages.error(request, "Failed to send OTP. Please try again.")
    else:
        form = ForgotPasswordForm()
    return render(request, 'firstApp/forgot_password.html', {'form': form})

def forgot_password_verify(request):
    email = request.session.get('otp_email')
    purpose = request.session.get('otp_purpose')
    
    if not email or purpose != 'reset_password':
        messages.error(request, "Session expired or invalid request.")
        return redirect('forgot_password')
        
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data['otp']
            try:
                otp_obj = EmailOTP.objects.filter(email=email).latest('created_at')
                success, message = otp_obj.verify(otp_entered)
                if success:
                    request.session['reset_password_verified'] = True
                    # Keep otp_email in session for the next step
                    del request.session['otp_purpose']
                    messages.success(request, "OTP verified. Please reset your password.")
                    return redirect('reset_password')
                else:
                    messages.error(request, message)
            except EmailOTP.DoesNotExist:
                messages.error(request, "Invalid OTP request.")
    else:
        form = OTPVerificationForm()
    return render(request, 'firstApp/forgot_password_verify.html', {'form': form, 'email': email})

def reset_password(request):
    email = request.session.get('otp_email')
    verified = request.session.get('reset_password_verified')
    
    if not email or not verified:
        messages.error(request, "Unauthorized access. Please verify OTP first.")
        return redirect('forgot_password')
        
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            try:
                user = CustomUser.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                
                # Cleanup session
                del request.session['otp_email']
                del request.session['reset_password_verified']
                
                messages.success(request, "Password reset successful! Please login with your new password.")
                return redirect('email_login')
            except CustomUser.DoesNotExist:
                messages.error(request, "User account not found.")
    else:
        form = ResetPasswordForm()
    return render(request, 'firstApp/reset_password.html', {'form': form})

def fetch_google_reviews():
    api_key = settings.GOOGLE_PLACES_API_KEY
    place_id = "ChIJgfA7KTUDYzkR6n9gjeGDYoI"

    if not api_key:
        print("Google Places API Key is missing.")
        return []

    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,rating,reviews&key={api_key}"

    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Google Places API Error: {response.status_code} - {response.text}")
            return []
            
        result = response.json()
        if "error_message" in result:
             print(f"Google Places API Error: {result['error_message']}")
             return []
             
        reviews = result.get("result", {}).get("reviews", [])
        return reviews
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []

def google_reviews(request):
    reviews = fetch_google_reviews()
    return render(request, "firstApp/reviews.html", {"reviews": reviews})

# --- Profile Password Change Views ---

@login_required
def initiate_profile_password_change(request):
    user = request.user
    if not user.email:
        messages.error(request, "Please add an email address to your profile to change password.")
        return redirect('profile')
        
    otp = EmailOTP.generate_otp()
    EmailOTP.objects.create(email=user.email, otp=otp)
    
    if send_otp_email(user.email, otp):
        request.session['password_change_otp_email'] = user.email
        request.session['password_change_verified'] = False
        messages.success(request, f"OTP sent to {user.email}")
        return redirect('verify_profile_password_change_otp')
    else:
        messages.error(request, "Failed to send OTP. Please try again.")
        return redirect('profile')

@login_required
def verify_profile_password_change_otp(request):
    email = request.session.get('password_change_otp_email')
    if not email or email != request.user.email:
        messages.error(request, "Invalid session. Please try again.")
        return redirect('profile')
        
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data['otp']
            try:
                otp_obj = EmailOTP.objects.filter(email=email).latest('created_at')
                success, message = otp_obj.verify(otp_entered)
                if success:
                    request.session['password_change_verified'] = True
                    return redirect('change_profile_password')
                else:
                    messages.error(request, message)
            except EmailOTP.DoesNotExist:
                messages.error(request, "Invalid OTP request.")
    else:
        form = OTPVerificationForm()
    return render(request, 'firstApp/profile_password_change_otp.html', {'form': form})

@login_required
def change_profile_password(request):
    if not request.session.get('password_change_verified'):
        messages.error(request, "Please verify OTP first.")
        return redirect('profile')
        
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST) 
        if form.is_valid():
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            
            # Cleanup
            del request.session['password_change_otp_email']
            del request.session['password_change_verified']
            
            # Keep user logged in
            login(request, user)
            
            messages.success(request, "Password changed successfully!")
            return redirect('profile')
    else:
        form = ResetPasswordForm()
        
    return render(request, 'firstApp/profile_password_change_form.html', {'form': form})
