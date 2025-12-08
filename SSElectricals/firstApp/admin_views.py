from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Appointment, AdminActivityLog, AdminSession, Order, Product, Category, ProductImage, OrderItem, Review, DailySales, DailyExpenditure
import os
from django.conf import settings
import pandas as pd
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from .forms import ProductForm, ReviewForm, DailySalesForm, DailyExpenditureForm
from django.core.mail import send_mail
from django.http import HttpResponse
from django.core.paginator import Paginator
import csv
import datetime
import json


@staff_member_required
def admin_dashboard(request):
    # 1. KPI Cards
    total_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    pending_appointments = Appointment.objects.filter(status='Pending').count()

    # 2. Charts Data
    # Daily Sales (Last 30 Days)
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    daily_sales = Order.objects.filter(created_at__gte=thirty_days_ago, status='Delivered') \
        .annotate(date=TruncDate('created_at')) \
        .values('date') \
        .annotate(sales=Sum('total_price')) \
        .order_by('date')
    
    dates = [str(x['date']) for x in daily_sales]
    sales = [float(x['sales'] or 0) for x in daily_sales]

    # Order Status Distribution
    status_counts = Order.objects.values('status').annotate(count=Count('id'))
    status_labels = [x['status'] for x in status_counts]
    status_data = [x['count'] for x in status_counts]

    # 3. Recent Tables
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    recent_appointments = Appointment.objects.order_by('-created_at')[:5]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'pending_appointments': pending_appointments,
        'dates_json': json.dumps(dates),
        'sales_json': json.dumps(sales),
        'status_labels_json': json.dumps(status_labels),
        'status_data_json': json.dumps(status_data),
        'recent_orders': recent_orders,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'admin/admin_dashboard.html', context)

@staff_member_required
def admin_activity_log_view(request):
    logs = AdminActivityLog.objects.select_related('admin').all().order_by('-timestamp')
    
    # Filters
    action_filter = request.GET.get('action')
    module_filter = request.GET.get('module')
    admin_filter = request.GET.get('admin')
    search_query = request.GET.get('search')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    if module_filter:
        logs = logs.filter(module=module_filter)
    if admin_filter:
        logs = logs.filter(admin_id=admin_filter)
    if search_query:
        logs = logs.filter(description__icontains=search_query)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 20) # Show 20 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Context Data
    from .models import CustomUser
    admins = CustomUser.objects.filter(is_staff=True)
    
    context = {
        'page_obj': page_obj,
        'action_choices': AdminActivityLog.ACTION_CHOICES,
        'module_choices': AdminActivityLog.MODULE_CHOICES,
        'admins': admins,
    }
    return render(request, 'admin/admin_activity_log.html', context)

@staff_member_required
def terminate_session(request, session_id):
    session = get_object_or_404(AdminSession, pk=session_id)
    session.delete()
    messages.success(request, "Session terminated.")
    return redirect('admin_dashboard')

@staff_member_required
def admin_appointment_list(request):
    appointments = Appointment.objects.all()
    return render(request, 'admin/admin_appointments.html', {'appointments': appointments})

@staff_member_required
def admin_appointment_update(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status:
            appointment.status = status
            appointment.save()
            messages.success(request, "Appointment updated successfully.")
            return redirect('admin_appointment_list')
    return render(request, 'admin/appointment_update.html', {'appointment': appointment})

@staff_member_required
def admin_appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.delete()
    messages.success(request, "Appointment deleted successfully.")
    return redirect('admin_appointment_list')

@staff_member_required
def admin_analytics(request):
    data_dir = os.path.join(settings.MEDIA_ROOT, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    xlsx_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
    
    context = {'files': xlsx_files}
    
    selected_file = request.GET.get('file')
    if selected_file and selected_file in xlsx_files:
        file_path = os.path.join(data_dir, selected_file)
        try:
            df = pd.read_excel(file_path)
            
            # Basic Analysis Logic (Assuming standard columns: 'Product', 'Quantity', 'Price', 'Delivery', 'Distance')
            # Adjust column names based on actual file structure or requirement
            # If columns don't exist, we just show raw data
            
            analysis = {}
            
            # Normalize column names to lowercase for safer access
            df.columns = df.columns.str.lower()
            
            # 1. Total Revenue
            if 'price' in df.columns:
                analysis['total_revenue'] = df['price'].sum()
            elif 'total' in df.columns:
                 analysis['total_revenue'] = df['total'].sum()
            else:
                 analysis['total_revenue'] = 0
                 
            # 2. Total Delivery Charges
            if 'delivery' in df.columns:
                analysis['total_delivery'] = df['delivery'].sum()
            elif 'delivery_charge' in df.columns:
                analysis['total_delivery'] = df['delivery_charge'].sum()
            else:
                analysis['total_delivery'] = 0
                
            # 3. Total Distance
            if 'distance' in df.columns:
                analysis['total_distance'] = df['distance'].sum()
            else:
                analysis['total_distance'] = 0

            # 4. Product Sales
            if 'product' in df.columns and 'quantity' in df.columns and 'price' in df.columns:
               product_sales = df.groupby('product').agg({'quantity': 'sum', 'price': 'sum'}).reset_index()
               product_sales.columns = ['name', 'quantity', 'sales']
               analysis['product_sales'] = product_sales.to_dict('records')
            else:
               analysis['product_sales'] = []

            # 5. Raw Data HTML
            analysis['html_table'] = df.to_html(classes='table table-bordered table-hover', index=False)
            
            context['analysis'] = analysis
            context['current_file'] = selected_file
            
        except Exception as e:
            context['error'] = f"Error processing file: {str(e)}"
            
    return render(request, 'admin/admin_analytics.html', context)

# ------------------------------------------------------------------
# Product Management
# ------------------------------------------------------------------

@staff_member_required
def admin_product_list(request):
    products = Product.objects.select_related('category').all().order_by('-created_at')
    return render(request, 'admin/admin_product_list.html', {'products': products})

@staff_member_required
def admin_product_add(request):
    if request.method == 'POST':
        # Manually handling form for simplicity or use Django Forms
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price') or None
        stock_quantity = request.POST.get('stock_quantity')
        brand = request.POST.get('brand')
        main_image = request.FILES.get('image')

        try:
            category = Category.objects.get(id=category_id)
            product = Product.objects.create(
                name=name,
                category=category,
                description=description,
                price=price,
                discount_price=discount_price,
                stock_quantity=stock_quantity,
                brand=brand,
                image=main_image
            )
            
            # Handle multiple images
            files = request.FILES.getlist('more_images')
            for f in files:
                ProductImage.objects.create(product=product, image=f)

            messages.success(request, f"Product '{name}' added successfully.")
            
            # Log Activity
            AdminActivityLog.objects.create(
                admin=request.user,
                action='CREATE',
                module='PRODUCT',
                description=f"Added product: {name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('admin_product_list')
        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")

    categories = Category.objects.all()
    return render(request, 'admin/admin_product_form.html', {'categories': categories})

@staff_member_required
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        dp = request.POST.get('discount_price')
        product.discount_price = dp if dp else None
        product.stock_quantity = request.POST.get('stock_quantity')
        product.brand = request.POST.get('brand')
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()

        # Handle multiple images (add more)
        files = request.FILES.getlist('more_images')
        for f in files:
            ProductImage.objects.create(product=product, image=f)

        messages.success(request, f"Product '{product.name}' updated successfully.")
        
        AdminActivityLog.objects.create(
            admin=request.user,
            action='UPDATE',
            module='PRODUCT',
            description=f"Updated product: {product.name}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return redirect('admin_product_list')

    categories = Category.objects.all()
    return render(request, 'admin/admin_product_form.html', {'product': product, 'categories': categories})

@staff_member_required
def admin_product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"Product '{name}' deleted.")
    
    AdminActivityLog.objects.create(
        admin=request.user,
        action='DELETE',
        module='PRODUCT',
        description=f"Deleted product: {name}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    return redirect('admin_product_list')

# ------------------------------------------------------------------
# Order Management
# ------------------------------------------------------------------

@staff_member_required
def admin_order_list(request):
    orders = Order.objects.select_related('user').all().order_by('-created_at')
    return render(request, 'admin/admin_order_list.html', {'orders': orders})

@staff_member_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        # Update Status
        if 'update_status' in request.POST:
            new_status = request.POST.get('status')
            order.status = new_status
            
            # If confirmed, maybe generate OTP? Or admin manually does it.
            # Requirement says: "Admin contacts user and finalizes price."
            if new_status == 'Confirmed':
                final_price = request.POST.get('final_price')
                delivery_charge = request.POST.get('delivery_charge')
                if final_price:
                    order.final_price = final_price
                if delivery_charge:
                    order.delivery_charge = delivery_charge
            
            # If Out for Delivery, generate OTP
            if new_status == 'Out for Delivery':
                import random
                otp = str(random.randint(100000, 999999))
                order.delivery_otp = otp
                # In real app, send SMS here
                messages.info(request, f"Delivery OTP generated: {otp}")
            
            # If Delivered, send Review Request Email
            if new_status == 'Delivered' and order.status != 'Delivered':
                try:
                    review_url = request.build_absolute_uri('/') + 'orders/' # Or product specific links
                    # We can link to order history where they can click products
                    
                    send_mail(
                        subject=f"Delivered: Order #{order.id} - Please Review Your Products",
                        message=f"Hi {order.user.first_name},\n\nYour order #{order.id} has been delivered successfully. We hope you like your products!\n\nPlease take a moment to review them to help others.\n\nVisit your order history to leave a review: {review_url}\n\nThank you,\nShiv Shakti Electrical",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[order.user.email],
                        fail_silently=True
                    )
                except Exception as e:
                    print("Email Error:", e)

            order.save()
            messages.success(request, f"Order status updated to {new_status}")
            
        return redirect('admin_order_detail', pk=pk)

    return render(request, 'admin/admin_order_detail.html', {'order': order})

# ------------------------------------------------------------------
# Review Management
# ------------------------------------------------------------------

@staff_member_required
def admin_reviews_list(request):
    reviews_list = Review.objects.select_related('product', 'user').all().order_by('-created_at')
    
    paginator = Paginator(reviews_list, 20)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)
    
    return render(request, 'admin/admin_reviews_list.html', {'reviews': reviews})

@staff_member_required
def admin_delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    messages.success(request, "Review deleted successfully.")
    return redirect('admin_reviews_list')

# ------------------------------------------------------------------
# Daily Sales Management
# ------------------------------------------------------------------

@staff_member_required
def admin_daily_sales(request):
    sales_list = DailySales.objects.all().order_by('-date')
    
    # Filters
    month = request.GET.get('month') # standard format YYYY-MM
    date = request.GET.get('date')
    
    if month:
        sales_list = sales_list.filter(date__month=month.split('-')[1], date__year=month.split('-')[0])
    if date:
        sales_list = sales_list.filter(date=date)

    paginator = Paginator(sales_list, 20)
    page_number = request.GET.get('page')
    sales_records = paginator.get_page(page_number)

    return render(request, 'admin/admin_daily_sales.html', {'sales_records': sales_records})

@staff_member_required
def admin_add_daily_sales(request):
    if request.method == 'POST':
        form = DailySalesForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.admin = request.user
            sale.save()
            messages.success(request, "Daily sales record added.")
            return redirect('admin_daily_sales')
    else:
        # Pre-fill date and day
        initial_data = {
            'date': timezone.now().date(),
            'day': timezone.now().strftime('%A')
        }
        form = DailySalesForm(initial=initial_data)
    
    return render(request, 'admin/admin_add_sales.html', {'form': form, 'title': 'Add Sales Entry'})

@staff_member_required
def admin_edit_daily_sales(request, pk):
    sale = get_object_or_404(DailySales, pk=pk)
    if request.method == 'POST':
        form = DailySalesForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Daily sales record updated.")
            return redirect('admin_daily_sales')
    else:
        form = DailySalesForm(instance=sale)
    return render(request, 'admin/admin_add_sales.html', {'form': form, 'title': 'Edit Sales Entry'})

@staff_member_required
def admin_delete_daily_sales(request, pk):
    sale = get_object_or_404(DailySales, pk=pk)
    sale.delete()
    messages.success(request, "Sales record deleted.")
    return redirect('admin_daily_sales')

@staff_member_required
def admin_export_sales(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="daily_sales.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Day', 'Total Sales', 'Online Received', 'Cash Received', 'Subtotal', 'Remark', 'Admin', 'Timestamp'])
    
    sales = DailySales.objects.all().order_by('-date')
    for sale in sales:
        writer.writerow([sale.date, sale.day, sale.total_sales, sale.online_received, sale.cash_received, sale.subtotal, sale.remark, sale.admin.username if sale.admin else 'Unknown', sale.created_at])
        
    return response

# ------------------------------------------------------------------
# Daily Expenditure Management
# ------------------------------------------------------------------

@staff_member_required
def admin_daily_expenses(request):
    expenses_list = DailyExpenditure.objects.all().order_by('-date')
    
    # Filters
    month = request.GET.get('month') 
    date = request.GET.get('date')
    
    if month:
        expenses_list = expenses_list.filter(date__month=month.split('-')[1], date__year=month.split('-')[0])
    if date:
        expenses_list = expenses_list.filter(date=date)

    paginator = Paginator(expenses_list, 20)
    page_number = request.GET.get('page')
    expenses = paginator.get_page(page_number)

    return render(request, 'admin/admin_daily_expenses.html', {'expenses': expenses})

@staff_member_required
def admin_add_daily_expense(request):
    if request.method == 'POST':
        form = DailyExpenditureForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.admin = request.user
            expense.save()
            messages.success(request, "Daily expenditure record added.")
            return redirect('admin_daily_expenses')
    else:
        initial_data = {
            'date': timezone.now().date(),
        }
        form = DailyExpenditureForm(initial=initial_data)
    
    return render(request, 'admin/admin_add_expense.html', {'form': form, 'title': 'Add Expense'})

@staff_member_required
def admin_edit_daily_expense(request, pk):
    expense = get_object_or_404(DailyExpenditure, pk=pk)
    if request.method == 'POST':
        form = DailyExpenditureForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Daily expenditure record updated.")
            return redirect('admin_daily_expenses')
    else:
        form = DailyExpenditureForm(instance=expense)
    return render(request, 'admin/admin_add_expense.html', {'form': form, 'title': 'Edit Expense'})

@staff_member_required
def admin_delete_daily_expense(request, pk):
    expense = get_object_or_404(DailyExpenditure, pk=pk)
    expense.delete()
    messages.success(request, "Expense record deleted.")
    return redirect('admin_daily_expenses')

@staff_member_required
def admin_export_expenses(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="daily_expenses.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Day', 'Amount', 'Payment Method', 'Description', 'Admin', 'Timestamp'])
    
    expenses = DailyExpenditure.objects.all().order_by('-date')
    for ex in expenses:
        writer.writerow([ex.date, ex.day, ex.amount, ex.payment_method, ex.description, ex.admin.username if ex.admin else 'Unknown', ex.created_at])
        
    return response
