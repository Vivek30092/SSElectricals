from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Appointment
from .forms import CustomUserCreationForm, CustomUserUpdateForm, CheckoutForm, AppointmentForm

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
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'firstApp/profile.html', {'form': form})

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
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('product_list')

    delivery_charge = 50
    total_amount = cart.total_price + delivery_charge

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['address']
            payment_method = form.cleaned_data['payment_method']
            upi_id = form.cleaned_data.get('upi_id', '')
            
            # Check stock availability
            for item in cart.items.all():
                if item.product.stock_quantity < item.quantity:
                    messages.error(request, f"{item.product.name} is out of stock or insufficient quantity available.")
                    return redirect('view_cart')
            
            # Create Order
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=total_amount,
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
            
            messages.success(request, "Order placed successfully!")
            return redirect('order_history')
    else:
        initial_data = {'address': request.user.address}
        form = CheckoutForm(initial=initial_data)
        
    return render(request, 'firstApp/checkout.html', {
        'form': form, 
        'cart': cart, 
        'delivery_charge': delivery_charge, 
        'total_amount': total_amount
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'firstApp/orders.html', {'orders': orders})

def about(request):
    return render(request, 'firstApp/about.html')

def contact(request):
    return render(request, 'firstApp/contact.html')

# Appointment Views
@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            if request.user.is_authenticated:
                appointment.user = request.user
            appointment.save()
            messages.success(request, "Appointment booked successfully!")
            return redirect('appointment_success')
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'customer_name': request.user.first_name + ' ' + request.user.last_name if request.user.first_name else request.user.username,
                'phone': request.user.phone_number,
                'email': request.user.email,
                'address': request.user.address,
                'city': 'Indore'
            }
        form = AppointmentForm(initial=initial_data)
    
    return render(request, 'firstApp/book_appointment.html', {'form': form})

def appointment_success(request):
    return render(request, 'firstApp/appointment_success.html')

@login_required
def my_appointments(request):
    appointments = Appointment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'firstApp/my_appointments.html', {'appointments': appointments})


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

# OTP Authentication Views
from .otp_service import OTPService
from .models import CustomUser, PhoneOTP, EmailOTP
from .forms import EmailSignupForm, EmailLoginForm, OTPVerificationForm
from .utils import send_otp_email

def otp_login(request):
    """Phone number input page for OTP login"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Validate phone number
        if not phone_number or len(phone_number) != 10 or not phone_number.isdigit():
            messages.error(request, "Please enter a valid 10-digit phone number")
            return render(request, 'firstApp/otp_login.html')
        
        # Check if user exists
        if not CustomUser.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "No account found with this phone number. Please signup first.")
            return render(request, 'firstApp/otp_login.html')
        
        # Send OTP
        success, message, otp = OTPService.send_otp(phone_number)
        
        if success:
            request.session['otp_phone'] = phone_number
            request.session['otp_purpose'] = 'login'
            messages.success(request, message)
            return redirect('otp_verify')
        else:
            messages.error(request, message)
    
    return render(request, 'firstApp/otp_login.html')

def otp_verify(request):
    """OTP verification page"""
    phone_number = request.session.get('otp_phone')
    purpose = request.session.get('otp_purpose', 'login')
    
    if not phone_number:
        messages.error(request, "Session expired. Please try again.")
        return redirect('otp_login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        
        if not otp_code or len(otp_code) != 6:
            messages.error(request, "Please enter a valid 6-digit OTP")
            return render(request, 'firstApp/otp_verify.html', {'phone_number': phone_number})
        
        # Verify OTP
        success, message = OTPService.verify_otp(phone_number, otp_code)
        
        if success:
            if purpose == 'login':
                # Login the user
                try:
                    user = CustomUser.objects.get(phone_number=phone_number)
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    messages.success(request, "Login successful!")
                    
                    # Clear session
                    del request.session['otp_phone']
                    del request.session['otp_purpose']
                    
                    return redirect('home')
                except CustomUser.DoesNotExist:
                    messages.error(request, "User not found")
            
            elif purpose == 'signup':
                messages.success(request, "Phone verified! Please complete your registration.")
                return redirect('signup_complete')
        else:
            messages.error(request, message)
    
    return render(request, 'firstApp/otp_verify.html', {'phone_number': phone_number})

def signup_otp(request):
    """Signup with OTP - Step 1: Collect phone and basic info"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Validate
        if not phone_number or len(phone_number) != 10 or not phone_number.isdigit():
            messages.error(request, "Please enter a valid 10-digit phone number")
            return render(request, 'firstApp/signup_otp.html')
        
        # Check if phone already exists
        if CustomUser.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "This phone number is already registered. Please login.")
            return redirect('otp_login')
        
        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'firstApp/signup_otp.html')
        
        # Send OTP
        success, message, otp = OTPService.send_otp(phone_number)
        
        if success:
            # Store data in session
            request.session['otp_phone'] = phone_number
            request.session['otp_purpose'] = 'signup'
            request.session['signup_data'] = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            }
            messages.success(request, message)
            return redirect('otp_verify')
        else:
            messages.error(request, message)
    
    return render(request, 'firstApp/signup_otp.html')

def signup_complete(request):
    """Complete signup after OTP verification"""
    phone_number = request.session.get('otp_phone')
    signup_data = request.session.get('signup_data')
    
    if not phone_number or not signup_data:
        messages.error(request, "Session expired. Please start again.")
        return redirect('signup_otp')
    
    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        
        try:
            # Create user
            user = CustomUser.objects.create_user(
                username=phone_number,  # Username same as phone
                phone_number=phone_number,
                email=signup_data['email'],
                first_name=signup_data['first_name'],
                last_name=signup_data['last_name'],
                address=address
            )
            
            # No password needed for OTP-based accounts
            user.set_unusable_password()
            user.save()
            
            # Auto-login
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            
            # Clear session
            del request.session['otp_phone']
            del request.session['otp_purpose']
            del request.session['signup_data']
            
            messages.success(request, "Account created successfully!")
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
    
    return render(request, 'firstApp/signup_complete.html', {'signup_data': signup_data})

def resend_otp(request):
    """AJAX endpoint to resend OTP"""
    if request.method == 'POST':
        phone_number = request.session.get('otp_phone')
        
        if not phone_number:
            return JsonResponse({'success': False, 'message': 'Session expired'})
        
        success, message, otp = OTPService.resend_otp(phone_number)
        return JsonResponse({'success': success, 'message': message})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

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
                        last_name=' '.join(data['full_name'].split(' ')[1:]) if ' ' in data['full_name'] else ''
                    )
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
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
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
                    user = CustomUser.objects.get(email=email)
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    del request.session['otp_email']
                    del request.session['otp_purpose']
                    messages.success(request, "Login successful!")
                    return redirect('home')
                else:
                    messages.error(request, message)
            except EmailOTP.DoesNotExist:
                messages.error(request, "Invalid OTP request.")
    else:
        form = OTPVerificationForm()
    return render(request, 'firstApp/login_email_otp_verify.html', {'form': form, 'email': email})
