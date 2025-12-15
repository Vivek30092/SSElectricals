from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.contrib.admin.views.decorators import staff_member_required # Keep for reference or fallback
from .decorators import admin_required, staff_required
from django.contrib import messages
from .models import Appointment, AdminActivityLog, AdminSession, Order, Product, Category, ProductImage, OrderItem, Review, DailySales, DailyExpenditure, PurchaseEntry, CustomUser
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
import numpy as np


@staff_required # Updated to custom decorator
def admin_dashboard(request):
    # 1. KPI Cards
    # Updated Dashboard Logic
    
    # Revenue from Orders
    order_revenue = Order.objects.filter(status='Delivered').aggregate(Sum('total_price'))['total_price__sum'] or 0
    # Revenue from Daily Sales (Offline)
    offline_sales = DailySales.objects.aggregate(Sum('total_sales'))['total_sales__sum'] or 0
    total_revenue = float(order_revenue) + float(offline_sales)

    # Expenses
    total_expenses = DailyExpenditure.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    online_expenses = DailyExpenditure.objects.filter(payment_method='Online').aggregate(Sum('amount'))['amount__sum'] or 0
    cash_expenses = DailyExpenditure.objects.filter(payment_method='Cash').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Purchases (Inventory Cost)
    total_purchases = PurchaseEntry.objects.aggregate(Sum('total_cost'))['total_cost__sum'] or 0

    profit_loss = total_revenue - float(total_expenses) - float(total_purchases)

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    pending_appointments = Appointment.objects.filter(status='Pending').count()

    # Charts Data
    today = timezone.now().date()
    
    # Date Range Filter logic
    range_option = request.GET.get('range', '30') # Default to 30 days
    start_date = None
    
    if range_option == '30':
        start_date = today - datetime.timedelta(days=30)
    elif range_option == '90':
         start_date = today - datetime.timedelta(days=90)
    elif range_option == '180':
         start_date = today - datetime.timedelta(days=180)
    elif range_option == '270':
         start_date = today - datetime.timedelta(days=270)
    elif range_option == '365':
         start_date = today - datetime.timedelta(days=365)
    elif range_option == '730':
         start_date = today - datetime.timedelta(days=730)
    elif range_option == '1095':
         start_date = today - datetime.timedelta(days=1095)
    elif range_option == 'all':
         start_date = None # All time
    else:
        start_date = today - datetime.timedelta(days=30)
        
    # Minimum date fallback if start_date is too recent (logic handled by start_date being None for ALL, or fixed range)
    # However, user requested "minimum 15 days view". If data is sparse, chart just shows what there is.
    
    # Fetch DailySales
    sales_qs = DailySales.objects.all()
    if start_date:
        sales_qs = sales_qs.filter(date__gte=start_date)
        
    daily_sales_data = sales_qs.values('date') \
        .annotate(sales=Sum('total_sales')) \
        .order_by('date')

    dates = [x['date'].strftime('%Y-%m-%d') for x in daily_sales_data]
    sales = [float(x['sales'] or 0) for x in daily_sales_data]

    # Category Statistics
    category_stats = Product.objects.values('category__name').annotate(count=Count('id')).order_by('-count')
    cat_labels = [x['category__name'] or 'Uncategorized' for x in category_stats]
    cat_data = [x['count'] for x in category_stats]

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    recent_appointments = Appointment.objects.order_by('-created_at')[:5]

    context = {
        'total_revenue': total_revenue,
        'order_revenue': order_revenue,
        'offline_sales': offline_sales,
        'total_expenses': total_expenses,
        'online_expenses': online_expenses,
        'cash_expenses': cash_expenses,
        'total_purchases': total_purchases,
        'profit_loss': profit_loss,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'pending_appointments': pending_appointments,
        'dates_json': json.dumps(dates),
        'sales_json': json.dumps(sales),
        'cat_labels_json': json.dumps(cat_labels),
        'cat_data_json': json.dumps(cat_data),
        'recent_orders': recent_orders,
        'recent_appointments': recent_appointments,
        'current_range': range_option,
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
        visiting_charge = request.POST.get('visiting_charge')
        extra_charge = request.POST.get('extra_charge')
        
        old_status = appointment.status

        if status:
            appointment.status = status
        
        if visiting_charge:
            appointment.visiting_charge = visiting_charge
            
        if extra_charge:
            appointment.extra_charge = extra_charge
            
        appointment.save()
        
        # Send Email Notification if status changed
        if old_status != appointment.status and appointment.email:
            try:
                subject = f"Appointment Update: {appointment.service_type} - {appointment.status}"
                
                # Interactive HTML Email
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
                        <div style="background-color: #0d6efd; color: white; padding: 20px; text-align: center;">
                            <h2 style="margin: 0;">Shiv Shakti Electrical</h2>
                            <p style="margin: 5px 0 0;">Service Update</p>
                        </div>
                        <div style="padding: 20px;">
                            <p>Dear {appointment.customer_name},</p>
                            <p>The status of your appointment for <strong>{appointment.service_type}</strong> has been updated.</p>
                            
                            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #0d6efd; margin: 20px 0;">
                                <p style="margin: 0;"><strong>New Status:</strong> <span style="color: #0d6efd; font-size: 18px; font-weight: bold;">{appointment.status}</span></p>
                                <p style="margin: 10px 0 0;"><strong>Date:</strong> {appointment.date} at {appointment.time}</p>
                                <p style="margin: 5px 0 0;"><strong>Total Charge:</strong> ₹{appointment.total_charge}</p>
                            </div>
                            
                            <p>If you have any questions, please contact us.</p>
                            <div style="text-align: center; margin-top: 30px;">
                                <a href="http://127.0.0.1:8000/contact/" style="background-color: #0d6efd; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Contact Support</a>
                            </div>
                        </div>
                        <div style="background-color: #eee; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                            &copy; {timezone.now().year} Shiv Shakti Electrical. All rights reserved.
                        </div>
                    </div>
                </body>
                </html>
                """
                
                send_mail(
                    subject=subject,
                    message=strip_tags(html_message), # Fallback text
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[appointment.email],
                    html_message=html_message,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Error sending appointment email: {e}")

        messages.success(request, "Appointment updated successfully.")
        return redirect('admin_appointment_list')
    return render(request, 'admin/appointment_update.html', {
        'appointment': appointment,
        'status_choices': Appointment.STATUS_CHOICES
    })

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

    # Handle File Upload
    if request.method == 'POST' and request.FILES.get('upload_file'):
        uploaded_file = request.FILES['upload_file']
        if uploaded_file.name.endswith(('.xlsx', '.tsv', '.csv')):
            fs = FileSystemStorage(location=data_dir)
            filename = fs.save(uploaded_file.name, uploaded_file)
            messages.success(request, f"File '{filename}' uploaded successfully.")
            return redirect('admin_analytics')
        else:
            messages.error(request, "Invalid file format. Please upload .xlsx, .tsv, or .csv.")
    
    data_files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.tsv', '.csv'))]
    
    context = {'files': data_files}
    
    selected_file = request.GET.get('file')
    if selected_file and selected_file in data_files:
        file_path = os.path.join(data_dir, selected_file)
        try:
            if selected_file.endswith('.tsv'):
                df = pd.read_csv(file_path, sep='\t')
            elif selected_file.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
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
            analysis['html_table'] = df.to_html(classes='table table-bordered table-hover mb-0', index=False)
            
            # 6. Trend Prediction (Linear Regression)
            if 'date' in df.columns:
                target_col = None
                if 'price' in df.columns: target_col = 'price'
                elif 'total' in df.columns: target_col = 'total'
                elif 'sales' in df.columns: target_col = 'sales'
                
                if target_col:
                    try:
                        # Prepare data
                        df_trend = df.copy()
                        df_trend['date'] = pd.to_datetime(df_trend['date'])
                        daily_data = df_trend.groupby('date')[target_col].sum().reset_index().sort_values('date')
                        
                        if len(daily_data) > 1:
                            # Create ordinal dates for regression
                            daily_data['ordinal'] = daily_data['date'].apply(lambda x: x.toordinal())
                            
                            X = daily_data['ordinal'].values
                            y = daily_data[target_col].values
                            
                            # Linear Regression: y = mx + c
                            slope, intercept = np.polyfit(X, y, 1)
                            
                            # Predictions for existing dates (Trend Line)
                            trend_values = slope * X + intercept
                            
                            # Future Predictions (Next 7 days)
                            last_date = daily_data['date'].max()
                            future_dates = [last_date + datetime.timedelta(days=i) for i in range(1, 8)]
                            future_ordinals = np.array([d.toordinal() for d in future_dates])
                            future_predictions = slope * future_ordinals + intercept
                            
                            # Prepare Labels and Data for Chart
                            # Labels: History + Future
                            history_dates_str = [d.strftime('%Y-%m-%d') for d in daily_data['date']]
                            future_dates_str = [d.strftime('%Y-%m-%d') for d in future_dates]
                            all_labels = history_dates_str + future_dates_str
                            
                            actual_data = list(daily_data[target_col]) + [None] * len(future_dates)
                            
                            # Trend Data: History Trend + Future Predictions
                            trend_line_data = list(trend_values) + list(future_predictions)
                            
                            analysis['chart_labels'] = json.dumps(all_labels)
                            analysis['chart_actual'] = json.dumps(actual_data)
                            analysis['chart_trend'] = json.dumps(trend_line_data)
                            analysis['has_prediction'] = True
                            
                    except Exception as reg_err:
                        print(f"Regression error: {reg_err}")
                        
            context['analysis'] = analysis
            context['current_file'] = selected_file
            
        except Exception as e:
            context['error'] = f"Error processing file: {str(e)}"
            
    return render(request, 'admin/admin_analytics.html', context)

@staff_member_required
def admin_delete_analytics_file(request):
    if request.method == 'POST':
        filename = request.POST.get('filename')
        if filename:
            data_dir = os.path.join(settings.MEDIA_ROOT, 'data')
            file_path = os.path.join(data_dir, filename)
            
            # Security check: ensure file is within data_dir
            # Using abspath for safer comparison
            abs_data_dir = os.path.abspath(data_dir)
            abs_file_path = os.path.abspath(file_path)
            
            if abs_file_path.startswith(abs_data_dir) and os.path.exists(abs_file_path):
                try:
                    os.remove(abs_file_path)
                    messages.success(request, f"File '{filename}' deleted successfully.")
                except Exception as e:
                    messages.error(request, f"Error deleting file: {e}")
            else:
                 messages.error(request, "Invalid file path.")
        else:
             messages.error(request, "No filename provided.")
             
    return redirect('admin_analytics')

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
        is_trending = request.POST.get('is_trending') == 'on'
        
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
                is_trending=is_trending,
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
        product.is_trending = request.POST.get('is_trending') == 'on'
        
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
            
            # Capture old status to detect change
            old_status = order.status
            
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
                # We save later, but for email logging relying on ID it's fine as Order exists.
                
                from .email_utils import send_delivery_otp_email
                send_delivery_otp_email(order, otp)
                
                messages.info(request, f"Delivery OTP generated and sent: {otp}")
            
            # Send status update email for ALL status changes (including Confirmed, Out for Delivery, etc)
            if new_status != old_status:
                from .email_utils import send_order_status_email, send_order_delivered_email
                
                if new_status == 'Delivered':
                    send_order_delivered_email(order)
                elif new_status == 'Out for Delivery':
                    # Already sent OTP email above
                    pass
                else:
                    send_order_status_email(order)

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

@staff_member_required
def admin_approve_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.is_approved = not review.is_approved
    review.save()
    status = "visible" if review.is_approved else "hidden"
    messages.success(request, f"Review is now {status}.")
    return redirect('admin_reviews_list')

# ------------------------------------------------------------------
# Daily Sales Management
# ------------------------------------------------------------------

@staff_member_required
def admin_daily_sales(request):
    sales_list = DailySales.objects.all().order_by('date')
    
    # Filters
    month = request.GET.get('month') # standard format YYYY-MM
    date = request.GET.get('date')
    year = request.GET.get('year')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    day_name = request.GET.get('day_name')
    
    if month:
        sales_list = sales_list.filter(date__month=month.split('-')[1], date__year=month.split('-')[0])
    if date:
        sales_list = sales_list.filter(date=date)
    if year:
        sales_list = sales_list.filter(date__year=year)
    if start_date and end_date:
        sales_list = sales_list.filter(date__range=[start_date, end_date])
    if day_name:
        sales_list = sales_list.filter(day__iexact=day_name.strip())
    
    # Calculate Totals
    total_sales = sales_list.aggregate(Sum('total_sales'))['total_sales__sum'] or 0
    total_online = sales_list.aggregate(Sum('online_received'))['online_received__sum'] or 0
    total_cash = sales_list.aggregate(Sum('cash_received'))['cash_received__sum'] or 0

    paginator = Paginator(sales_list, 20)
    page_number = request.GET.get('page')
    sales_records = paginator.get_page(page_number)

    context = {
        'sales_records': sales_records,
        'total_sales': total_sales,
        'total_online': total_online,
        'total_cash': total_cash
    }

    return render(request, 'admin/admin_daily_sales.html', context)

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
    expenses_list = DailyExpenditure.objects.all().order_by('date', 'created_at')
    
    # Filters
    month = request.GET.get('month')
    date = request.GET.get('date')
    year = request.GET.get('year')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    day_name = request.GET.get('day_name')
    
    if month:
        expenses_list = expenses_list.filter(date__month=month.split('-')[1], date__year=month.split('-')[0])
    if date:
        expenses_list = expenses_list.filter(date=date)
    if year:
        expenses_list = expenses_list.filter(date__year=year)
    if start_date and end_date:
        expenses_list = expenses_list.filter(date__range=[start_date, end_date])
    if day_name:
        expenses_list = expenses_list.filter(day__iexact=day_name.strip())

    # Calculate Totals
    total_expenses = expenses_list.aggregate(Sum('amount'))['amount__sum'] or 0
    total_online_expenses = expenses_list.filter(payment_method='Online').aggregate(Sum('amount'))['amount__sum'] or 0
    total_cash_expenses = expenses_list.filter(payment_method='Cash').aggregate(Sum('amount'))['amount__sum'] or 0

    paginator = Paginator(expenses_list, 20)
    page_number = request.GET.get('page')
    expenses = paginator.get_page(page_number)

    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'total_online_expenses': total_online_expenses,
        'total_cash_expenses': total_cash_expenses
    }

    return render(request, 'admin/admin_daily_expenses.html', context)

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
def admin_export_sales(request):
    fmt = request.GET.get('format', 'csv')
    sales = DailySales.objects.all().order_by('-date')
    
    # Define columns
    columns = ['Date', 'Day', 'Total Sales', 'Online', 'Cash', 'Remark', 'Admin']
    data = []
    for sale in sales:
        data.append([
            str(sale.date), 
            sale.day, 
            str(sale.total_sales), 
            str(sale.online_received), 
            str(sale.cash_received), 
            sale.remark, 
            sale.admin.username if sale.admin else 'Unknown'
        ])

    if fmt == 'tsv':
        response = HttpResponse(content_type='text/tab-separated-values')
        response['Content-Disposition'] = 'attachment; filename="daily_sales.tsv"'
        writer = csv.writer(response, delimiter='\t')
        writer.writerow(columns)
        for row in data:
            writer.writerow(row)
        return response

    elif fmt == 'pdf':
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="daily_sales.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph("Daily Sales Report", styles['Title']))
        
        table_data = [columns] + data
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        doc.build(elements)
        return response

    elif fmt == 'word':
        from docx import Document
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = 'attachment; filename="daily_sales.docx"'
        
        doc = Document()
        doc.add_heading('Daily Sales Report', 0)
        
        table = doc.add_table(rows=1, cols=len(columns))
        hdr_cells = table.rows[0].cells
        for i, col in enumerate(columns):
            hdr_cells[i].text = col
            
        for row in data:
            row_cells = table.add_row().cells
            for i, val in enumerate(row):
                row_cells[i].text = str(val)
                
        doc.save(response)
        return response

    else: # Default CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="daily_sales.csv"'
        writer = csv.writer(response)
        writer.writerow(columns)
        for row in data:
            writer.writerow(row)
        return response

@staff_member_required
def admin_export_expenses(request):
    fmt = request.GET.get('format', 'csv')
    expenses = DailyExpenditure.objects.all().order_by('-date')
    
    columns = ['Date', 'Day', 'Amount', 'Method', 'Description', 'Admin']
    data = []
    for ex in expenses:
        data.append([
            str(ex.date), 
            ex.day, 
            str(ex.amount), 
            ex.payment_method, 
            ex.description, 
            ex.admin.username if ex.admin else 'Unknown'
        ])

    if fmt == 'tsv':
        response = HttpResponse(content_type='text/tab-separated-values')
        response['Content-Disposition'] = 'attachment; filename="daily_expenses.tsv"'
        writer = csv.writer(response, delimiter='\t')
        writer.writerow(columns)
        for row in data:
            writer.writerow(row)
        return response
        
    elif fmt == 'pdf':
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="daily_expenses.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Daily Expenses Report", styles['Title']))
        
        table_data = [columns] + data
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        doc.build(elements)
        return response

    elif fmt == 'word':
        from docx import Document
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = 'attachment; filename="daily_expenses.docx"'
        
        doc = Document()
        doc.add_heading('Daily Expenses Report', 0)
        
        table = doc.add_table(rows=1, cols=len(columns))
        hdr_cells = table.rows[0].cells
        for i, col in enumerate(columns):
            hdr_cells[i].text = col
            
        for row in data:
            row_cells = table.add_row().cells
            for i, val in enumerate(row):
                row_cells[i].text = str(val)
                
        doc.save(response)
        return response

    else: # Default CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="daily_expenses.csv"'
        writer = csv.writer(response)
        writer.writerow(columns)
        for row in data:
            writer.writerow(row)
        return response

# ------------------------------------------------------------------
# Category Management
# ------------------------------------------------------------------

@staff_member_required
def admin_category_list(request):
    categories = Category.objects.annotate(product_count=Count('products')).all()
    return render(request, 'admin/admin_category_list.html', {'categories': categories})

@staff_member_required
def admin_category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        
        if name:
            Category.objects.create(name=name, image=image)
            messages.success(request, "Category created successfully.")
            return redirect('admin_category_list')
        
    return render(request, 'admin/admin_category_form.html')

@staff_member_required
def admin_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
        category.save()
        messages.success(request, "Category updated successfully.")
        return redirect('admin_category_list')
        
    return render(request, 'admin/admin_category_form.html', {'category': category})

@staff_member_required
def admin_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    messages.success(request, "Category deleted.")
    return redirect('admin_category_list')

# ------------------------------------------------------------------
# File Upload & Bulk Operations
# ------------------------------------------------------------------

def validate_columns(df, required):
    # Normalize columns: strip, lower, replace space with underscore
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(' ', '_')
    missing = [c for c in required if c not in df.columns]
    return missing

@staff_member_required
def admin_upload_sales(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('.tsv'):
                df = pd.read_csv(file, sep='\t')
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                messages.error(request, "Invalid file format. Please upload CSV, TSV, or XLSX.")
                return redirect('admin_daily_sales')

            required = ['date', 'total_sales']
            missing = validate_columns(df, required)
            if missing:
                messages.error(request, f"Missing required columns: {', '.join(missing)}")
                return redirect('admin_daily_sales')
                
            count = 0
            for _, row in df.iterrows():
                try:
                    date_val = pd.to_datetime(row['date']).date()
                    DailySales.objects.update_or_create(
                        date=date_val,
                        defaults={
                            'total_sales': row.get('total_sales', 0),
                            'online_received': row.get('online_received', 0),
                            'cash_received': row.get('cash_received', 0),
                            'remark': row.get('remark', 'Updated via Upload'),
                            'admin': request.user
                        }
                    )
                    count += 1
                except Exception as row_err:
                    print(f"Skipping row: {row_err}")

            messages.success(request, f"Successfully processed {count} sales records.")
            return redirect('admin_daily_sales')
            
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            return redirect('admin_daily_sales')
            
    return render(request, 'admin/admin_upload_form.html', {'title': 'Upload Daily Sales (CSV/TSV/XLSX)'})

@staff_member_required
def admin_upload_expenses(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('.tsv'):
                df = pd.read_csv(file, sep='\t')
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                messages.error(request, "Invalid file format. Please upload CSV, TSV, or XLSX.")
                return redirect('admin_daily_expenses')

            # Required: Date, Amount, Payment Method, Description
            # Mappable column names
            required = ['date', 'amount']
            missing = validate_columns(df, required)
            if missing:
                messages.error(request, f"Missing required columns: {', '.join(missing)}")
                return redirect('admin_daily_expenses')
                
            count = 0
            for _, row in df.iterrows():
                try:
                    date_val = pd.to_datetime(row['date']).date()
                    DailyExpenditure.objects.create(
                        date=date_val,
                        amount=row['amount'],
                        payment_method=row.get('payment_method', 'Cash'), # Default to Cash if missing
                        description=row.get('description', 'Imported Expense'),
                        admin=request.user
                    )
                    count += 1
                except Exception as row_err:
                    print(f"Skipping row: {row_err}")
                    
            messages.success(request, f"Successfully imported {count} expense records.")
            return redirect('admin_daily_expenses')
            
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            return redirect('admin_daily_expenses')
            
    return render(request, 'admin/admin_upload_form.html', {'title': 'Upload Daily Expenses (CSV/TSV/XLSX)'})




# ------------------------------------------------------------------
# User Management
# ------------------------------------------------------------------

@staff_member_required
def admin_user_list(request):
    # Filter for regular users (not superusers or staff) if desired, or all
    # Let's show all users but maybe visually distinguish
    users_list = CustomUser.objects.filter(is_superuser=False, is_staff=False).order_by('-date_joined')
    
    paginator = Paginator(users_list, 20)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    return render(request, 'admin/admin_user_list.html', {'users': users})

@staff_member_required
def admin_user_detail(request, user_id):
    from .models import CustomUser 
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Cart
    try:
        cart_items = user.cart.items.all()
        cart_total = user.cart.total_price
    except:
        cart_items = []
        cart_total = 0
        
    # Wishlist
    # Wishlist is ForeignKey in models.py: user = models.ForeignKey(..., related_name='wishlist')
    wishlist_items = user.wishlist.all()
    
    # Orders (Optional but useful)
    orders = user.orders.all().order_by('-created_at')[:5]
    
    context = {
        'customer': user,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'wishlist_items': wishlist_items,
        'recent_orders': orders
    }
    
    return render(request, 'admin/admin_user_detail.html', context)
