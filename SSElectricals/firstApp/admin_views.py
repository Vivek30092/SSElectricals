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
    """
    Admin Dashboard - Financial Metrics
    
    CRITICAL BUSINESS RULE (Non-Negotiable):
    ========================================
    All financial metrics (revenue, sales, profit) are calculated EXCLUSIVELY from:
      - Manual DailySales entries
      - Manual DailyExpenditure entries
      - Manual PurchaseEntry records
    
    Orders and deliveries are OPERATIONAL records only.
    They do NOT affect financial calculations under any circumstances.
    
    This ensures:
      - Clean separation between operations and accounting
      - Accurate real-world financial tracking
      - No accidental double-counting
      - Admin retains full control of business numbers
    """
    
    # ==================================================================================
    # FINANCIAL METRICS - MANUAL ENTRY ONLY (NO ORDER DATA)
    # ==================================================================================
    
    # Total Revenue: ONLY from manually entered daily sales
    total_revenue = DailySales.objects.aggregate(Sum('total_sales'))['total_sales__sum'] or 0
    
    # Cash vs Online breakdown from manual sales entries
    total_cash_received = DailySales.objects.aggregate(Sum('cash_received'))['cash_received__sum'] or 0
    total_online_received = DailySales.objects.aggregate(Sum('online_received'))['online_received__sum'] or 0


    # Expenses: From manual daily expenditure entries (using combined online + cash model)
    total_expenses = DailyExpenditure.objects.aggregate(Sum('total'))['total__sum'] or 0
    online_expenses = DailyExpenditure.objects.aggregate(Sum('online_amount'))['online_amount__sum'] or 0
    cash_expenses = DailyExpenditure.objects.aggregate(Sum('cash_amount'))['cash_amount__sum'] or 0
    
    # Purchases (Inventory Cost): From manual purchase entries
    total_purchases = PurchaseEntry.objects.aggregate(Sum('total_cost'))['total_cost__sum'] or 0

    # Net Profit Calculation: Revenue - Expenses - Purchases (NO ORDER DATA)
    profit_loss = float(total_revenue) - float(total_expenses) - float(total_purchases)

    # ==================================================================================
    # OPERATIONAL METRICS (FOR REFERENCE ONLY - NOT USED IN FINANCIAL CALCULATIONS)
    # ==================================================================================
    
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    pending_appointments = Appointment.objects.filter(status='Pending').count()

    # ==================================================================================
    # SALES TREND CHART DATA (FROM MANUAL DAILY SALES ONLY)
    # ==================================================================================
    
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
    
    # Fetch DailySales for chart
    sales_qs = DailySales.objects.all()
    if start_date:
        sales_qs = sales_qs.filter(date__gte=start_date)
        
    daily_sales_data = sales_qs.values('date') \
        .annotate(sales=Sum('total_sales')) \
        .order_by('date')

    dates = [x['date'].strftime('%Y-%m-%d') for x in daily_sales_data]
    sales = [float(x['sales'] or 0) for x in daily_sales_data]

    # Fetch DailyExpenditure for comparison chart
    expenses_qs = DailyExpenditure.objects.all()
    if start_date:
        expenses_qs = expenses_qs.filter(date__gte=start_date)
    
    daily_expenses_data = expenses_qs.values('date') \
        .annotate(expense=Sum('total')) \
        .order_by('date')
    
    # Create a dictionary for quick lookup
    expenses_dict = {x['date'].strftime('%Y-%m-%d'): float(x['expense'] or 0) for x in daily_expenses_data}
    
    # Match expenses to sales dates (fill with 0 if no expense for that date)
    expenses = [expenses_dict.get(date, 0) for date in dates]

    # Category Statistics (for product management reference)
    category_stats = Product.objects.values('category__name').annotate(count=Count('id')).order_by('-count')
    cat_labels = [x['category__name'] or 'Uncategorized' for x in category_stats]
    cat_data = [x['count'] for x in category_stats]

    # Recent operational records (for quick reference)
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    recent_appointments = Appointment.objects.order_by('-created_at')[:10]

    context = {
        # Financial Metrics (Manual Entry Only)
        'total_revenue': total_revenue,
        'total_cash_received': total_cash_received,
        'total_online_received': total_online_received,
        'total_expenses': total_expenses,
        'online_expenses': online_expenses,
        'cash_expenses': cash_expenses,
        'total_purchases': total_purchases,
        'profit_loss': profit_loss,
        
        # Operational Metrics (Not used in financial calculations)
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'pending_appointments': pending_appointments,
        
        # Chart Data (From Manual Sales Only)
        'dates_json': json.dumps(dates),
        'sales_json': json.dumps(sales),
        'expenses_json': json.dumps(expenses),
        'cat_labels_json': json.dumps(cat_labels),
        'cat_data_json': json.dumps(cat_data),
        
        # Quick Reference
        'recent_orders': recent_orders,
        'recent_appointments': recent_appointments,
        'current_range': range_option,
    }
    return render(request, 'admin/admin_dashboard.html', context)

@staff_required
def admin_analytics_new(request):
    """Working Analytics Dashboard"""
    from django.db.models import Sum, Avg
    from decimal import Decimal
    import json
    
    # Direct queries - get ALL data
    from firstApp.models import DailySales, DailyExpenditure
    
    # Get totals with proper Decimal handling (no Avg to avoid naming conflicts)
    sales_agg = DailySales.objects.aggregate(
        total=Sum('total_sales'),
        online=Sum('online_received'),
        cash=Sum('cash_received'),
        labor=Sum('labor_charge'),
        delivery=Sum('delivery_charge')
    )
    
    expense_agg = DailyExpenditure.objects.aggregate(
        total=Sum('total'),
        online=Sum('online_amount'),
        cash=Sum('cash_amount')
    )
    
    # Get counts for manual average calculation
    sales_count = DailySales.objects.count()
    expense_count = DailyExpenditure.objects.count()
    
    # Convert Decimal to float safely
    def safe_float(val):
        return float(val) if val else 0.0
    
    total_sales = safe_float(sales_agg['total'])
    total_online_sales = safe_float(sales_agg['online'])
    total_cash_sales = safe_float(sales_agg['cash'])
    total_labor = safe_float(sales_agg['labor'])
    total_delivery = safe_float(sales_agg['delivery'])
    
    total_expense = safe_float(expense_agg['total'])
    total_online_exp = safe_float(expense_agg['online'])
    total_cash_exp = safe_float(expense_agg['cash'])
    
    # Calculate averages manually
    avg_sales = (total_sales / sales_count) if sales_count > 0 else 0.0
    avg_expense = (total_expense / expense_count) if expense_count > 0 else 0.0
    
    # Calculate percentages
    online_pct = (total_online_sales / total_sales * 100) if total_sales > 0 else 0
    cash_pct = (total_cash_sales / total_sales * 100) if total_sales > 0 else 0
    online_exp_pct = (total_online_exp / total_expense * 100) if total_expense > 0 else 0
    cash_exp_pct = (total_cash_exp / total_expense * 100) if total_expense > 0 else 0
    
    # Get all sales for charts and min/max
    all_sales = DailySales.objects.all().order_by('date').values('date', 'total_sales')
    sales_dates = [s['date'].strftime('%Y-%m-%d') for s in all_sales]
    sales_values = [safe_float(s['total_sales']) for s in all_sales]
    
    # Find min/max sales days
    min_sale_day = DailySales.objects.order_by('total_sales').first()
    max_sale_day = DailySales.objects.order_by('-total_sales').first()
    
    # Calculate daily average (already have it)
    daily_avg_sales = avg_sales
    
    # For monthly - need to aggregate by month
    from django.db.models.functions import TruncMonth
    monthly_sales = DailySales.objects.annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('total_sales')
    ).order_by('month')
    
    monthly_sales_list = list(monthly_sales)
    if monthly_sales_list:
        monthly_values = [safe_float(m['total']) for m in monthly_sales_list]
        monthly_avg_sales = sum(monthly_values) / len(monthly_values) if monthly_values else 0
        
        # Prepare data for monthly chart
        monthly_sales_labels = [m['month'].strftime('%b %Y') for m in monthly_sales_list]
        monthly_sales_values = monthly_values
        
        # Find best month
        max_month = max(monthly_sales_list, key=lambda x: safe_float(x['total']))
        max_sales_month = max_month['month'].strftime('%B %Y')
        max_sales_month_value = safe_float(max_month['total'])
        
        min_month = min(monthly_sales_list, key=lambda x: safe_float(x['total']))
        min_sales_month = min_month['month'].strftime('%B %Y')
        min_sales_month_value = safe_float(min_month['total'])
    else:
        monthly_avg_sales = 0
        monthly_sales_labels = []
        monthly_sales_values = []
        max_sales_month = 'N/A'
        max_sales_month_value = 0
        min_sales_month = 'N/A'
        min_sales_month_value = 0
    
    # Quarterly aggregation
    from django.db.models.functions import TruncQuarter
    quarterly_sales = DailySales.objects.annotate(
        quarter=TruncQuarter('date')
    ).values('quarter').annotate(
        total=Sum('total_sales')
    ).order_by('quarter')
    
    quarterly_list = list(quarterly_sales)
    quarterly_labels = []
    quarterly_values = []
    for q in quarterly_list:
        quarter_date = q['quarter']
        quarter_num = (quarter_date.month - 1) // 3 + 1
        label = f"Q{quarter_num} {quarter_date.year}"
        quarterly_labels.append(label)
        quarterly_values.append(safe_float(q['total']))
    
    # Yearly aggregation
    from django.db.models.functions import TruncYear
    yearly_sales = DailySales.objects.annotate(
        year=TruncYear('date')
    ).values('year').annotate(
        total=Sum('total_sales')
    ).order_by('year')
    
    yearly_list = list(yearly_sales)
    yearly_labels = [y['year'].strftime('%Y') for y in yearly_list]
    yearly_values = [safe_float(y['total']) for y in yearly_list]
    
    # Weekday aggregation
    from django.db.models import Case, When, Value, CharField
    weekday_sales = DailySales.objects.values('day').annotate(
        total=Sum('total_sales')
    ).order_by()  # Remove default ordering
    
    # Order by weekday
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_dict = {w['day']: safe_float(w['total']) for w in weekday_sales}
    weekday_labels = weekday_order
    weekday_values = [weekday_dict.get(day, 0) for day in weekday_order]
    
    all_expenses = DailyExpenditure.objects.all().order_by('date').values('date', 'total')
    expense_dates = [e['date'].strftime('%Y-%m-%d') for e in all_expenses]
    expense_values = [safe_float(e['total']) for e in all_expenses]
    
    context = {
        'total_sales': total_sales,
        'total_expense': total_expense,
        'total_online_sales': total_online_sales,
        'total_cash_sales': total_cash_sales,
        'avg_sales': avg_sales,
        'online_pct': round(online_pct, 1),
        'cash_pct': round(cash_pct, 1),
        'total_labor': total_labor,
        'total_delivery': total_delivery,
        'avg_expense': avg_expense,
        'total_online_exp': total_online_exp,
        'total_cash_exp': total_cash_exp,
        'online_exp_pct': round(online_exp_pct, 1),
        'cash_exp_pct': round(cash_exp_pct, 1),
        'start_date': None,
        'end_date': None,
        'month': None,
        'time_view': 'daily',
        'sales_dates_json': json.dumps(sales_dates),
        'sales_values_json': json.dumps(sales_values),
        'expense_dates_json': json.dumps(expense_dates),
        'expense_values_json': json.dumps(expense_values),
        'monthly_sales_labels_json': json.dumps(monthly_sales_labels),
        'monthly_sales_values_json': json.dumps(monthly_sales_values),
        'monthly_expense_labels_json': json.dumps([]),
        'monthly_expense_values_json': json.dumps([]),
        'quarterly_labels_json': json.dumps(quarterly_labels),
        'quarterly_values_json': json.dumps(quarterly_values),
        'yearly_labels_json': json.dumps(yearly_labels),
        'yearly_values_json': json.dumps(yearly_values),
        'weekday_labels_json': json.dumps(weekday_labels),
        'weekday_values_json': json.dumps(weekday_values),
        'min_sale_day': min_sale_day,
        'max_sale_day': max_sale_day,
        'min_expense_day': None,
        'max_expense_day': None,
        'min_sales_month': min_sales_month,
        'min_sales_month_value': min_sales_month_value,
        'max_sales_month': max_sales_month,
        'max_sales_month_value': max_sales_month_value,
        'daily_avg_sales': daily_avg_sales,
        'monthly_avg_sales': monthly_avg_sales,
        'quarterly_avg_sales': 0,
        'yearly_avg_sales': 0,
        'monthly_avg_expense': 0,
        'best_month_info': None,
        'worst_month_info': None,
        'net_contribution': total_sales - total_labor - total_delivery - total_expense,
        'contribution_color': 'success',
    }
    
    return render(request, 'admin/admin_analytics.html', context)
    from django.db.models.functions import TruncMonth, TruncDate, TruncQuarter, TruncYear
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    import json
    from datetime import datetime, timedelta
    from django.utils import timezone
    import calendar
    
    # ==================== FILTERS ====================
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    month = request.GET.get('month')
    time_view = request.GET.get('time_view', 'monthly')  # daily, monthly, quarterly, half_yearly, yearly
    export_format = request.GET.get('export')  # pdf, excel, csv, png
    
    # Parse dates
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except:
            pass
    
    # Default: Show all data (no date filter)
    # Users can apply filters manually if needed
    # if not start_date and not end_date and not month:
    #     end_date = timezone.now().date()
    #     start_date = end_date - timedelta(days=365)
    
    # Build querysets
    sales_qs = DailySales.objects.all()
    expenses_qs = DailyExpenditure.objects.all()
    
    if start_date:
        sales_qs = sales_qs.filter(date__gte=start_date)
        expenses_qs = expenses_qs.filter(date__gte=start_date)
    if end_date:
        sales_qs = sales_qs.filter(date__lte=end_date)
        expenses_qs = expenses_qs.filter(date__lte=end_date)
    if month:
        year, mon = month.split('-')
        sales_qs = sales_qs.filter(date__year=year, date__month=mon)
        expenses_qs = expenses_qs.filter(date__year=year, date__month=mon)
    
    # DEBUG: Print what we're querying
    import sys
    print("=" * 80, flush=True)
    print(f"DEBUG Analytics: Date range: {start_date} to {end_date}", flush=True)
    print(f"DEBUG Analytics: Sales count: {sales_qs.count()}", flush=True)
    print(f"DEBUG Analytics: Expenses count: {expenses_qs.count()}", flush=True)
    print(f"DEBUG Analytics: Sales QS: {sales_qs.query}", flush=True)
    print("=" * 80, flush=True)
    sys.stdout.flush()
    
    # ==================== BASIC KPIs ====================
    sales_totals = sales_qs.aggregate(
        total_sales=Sum('total_sales'),
        total_online=Sum('online_received'),
        total_cash=Sum('cash_received'),
        total_labor=Sum('labor_charge'),
        total_delivery=Sum('delivery_charge'),
        avg_sales=Avg('total_sales'),
        min_sale=Min('total_sales'),
        max_sale=Max('total_sales')
    )
    
    total_sales = float(sales_totals['total_sales'] or 0)
    avg_sales = float(sales_totals['avg_sales'] or 0)
    total_online_sales = float(sales_totals['total_online'] or 0)
    total_cash_sales = float(sales_totals['total_cash'] or 0)
    total_labor = float(sales_totals['total_labor'] or 0)
    total_delivery = float(sales_totals['total_delivery'] or 0)
    
    print(f"DEBUG Analytics: Total sales value: {total_sales}")
    
    online_pct = (total_online_sales / total_sales * 100) if total_sales > 0 else 0
    cash_pct = (total_cash_sales / total_sales * 100) if total_sales > 0 else 0
    
    expense_totals = expenses_qs.aggregate(
        total_expense=Sum('total'),
        total_online_exp=Sum('online_amount'),
        total_cash_exp=Sum('cash_amount'),
        avg_expense=Avg('total'),
        min_expense=Min('total'),
        max_expense=Max('total')
    )
    
    total_expense = float(expense_totals['total_expense'] or 0)
    avg_expense = float(expense_totals['avg_expense'] or 0)
    total_online_exp = float(expense_totals['total_online_exp'] or 0)
    total_cash_exp = float(expense_totals['total_cash_exp'] or 0)
    
    online_exp_pct = (total_online_exp / total_expense * 100) if total_expense > 0 else 0
    cash_exp_pct = (total_cash_exp / total_expense * 100) if total_expense > 0 else 0
    
    # ==================== MIN/MAX DETECTION ====================
    # Find min/max sales days
    min_sale_day = sales_qs.filter(total_sales=sales_totals['min_sale']).first()
    max_sale_day = sales_qs.filter(total_sales=sales_totals['max_sale']).first()
    
    # Find min/max expense days
    min_expense_day = expenses_qs.filter(total=expense_totals['min_expense']).first()
    max_expense_day = expenses_qs.filter(total=expense_totals['max_expense']).first()
    
    # ==================== TIME-BASED AGGREGATIONS ====================
    
    # MONTHLY DATA
    monthly_sales = sales_qs.annotate(month=TruncMonth('date')).values('month').annotate(
        total=Sum('total_sales'),
        online=Sum('online_received'),
        cash=Sum('cash_received'),
        labor=Sum('labor_charge'),
        delivery=Sum('delivery_charge')
    ).order_by('month')
    
    monthly_sales_list = list(monthly_sales)
    monthly_sales_labels = [x['month'].strftime('%B %Y') for x in monthly_sales_list]
    monthly_sales_values = [float(x['total'] or 0) for x in monthly_sales_list]
    
    # Calculate month-on-month growth
    monthly_growth = []
    for i in range(len(monthly_sales_values)):
        if i == 0:
            monthly_growth.append(0)
        else:
            prev = monthly_sales_values[i-1]
            curr = monthly_sales_values[i]
            growth = ((curr - prev) / prev * 100) if prev > 0 else 0
            monthly_growth.append(round(growth, 2))
    
    monthly_expenses = expenses_qs.annotate(month=TruncMonth('date')).values('month').annotate(
        total=Sum('total'),
        online=Sum('online_amount'),
        cash=Sum('cash_amount')
    ).order_by('month')
    
    monthly_expense_list = list(monthly_expenses)
    monthly_expense_labels = [x['month'].strftime('%B %Y') for x in monthly_expense_list]
    monthly_expense_values = [float(x['total'] or 0) for x in monthly_expense_list]
    
    # Monthly averages
    monthly_avg_sales = sum(monthly_sales_values) / len(monthly_sales_values) if monthly_sales_values else 0
    monthly_avg_expense = sum(monthly_expense_values) / len(monthly_expense_values) if monthly_expense_values else 0
    
    # Find min/max months
    if monthly_sales_list:
        max_month_data = max(monthly_sales_list, key=lambda x: x['total'] or 0)
        min_month_data = min(monthly_sales_list, key=lambda x: x['total'] or 0)
        max_sales_month = max_month_data['month'].strftime('%B %Y')
        max_sales_month_value = float(max_month_data['total'] or 0)
        min_sales_month = min_month_data['month'].strftime('%B %Y')
        min_sales_month_value = float(min_month_data['total'] or 0)
    else:
        max_sales_month = min_sales_month = "N/A"
        max_sales_month_value = min_sales_month_value = 0
    
    # QUARTERLY DATA
    quarterly_sales = sales_qs.annotate(quarter=TruncQuarter('date')).values('quarter').annotate(
        total=Sum('total_sales')
    ).order_by('quarter')
    
    quarterly_sales_list = list(quarterly_sales)
    quarterly_labels = []
    quarterly_values = []
    
    for q in quarterly_sales_list:
        quarter_num = (q['quarter'].month - 1) // 3 + 1
        label = f"Q{quarter_num} {q['quarter'].year}"
        quarterly_labels.append(label)
        quarterly_values.append(float(q['total'] or 0))
    
    # Quarter-on-quarter growth
    quarterly_growth = []
    for i in range(len(quarterly_values)):
        if i == 0:
            quarterly_growth.append(0)
        else:
            prev = quarterly_values[i-1]
            curr = quarterly_values[i]
            growth = ((curr - prev) / prev * 100) if prev > 0 else 0
            quarterly_growth.append(round(growth, 2))
    
    quarterly_avg_sales = sum(quarterly_values) / len(quarterly_values) if quarterly_values else 0
    
    # HALF-YEARLY DATA
    half_yearly_sales = []
    yearly_data = sales_qs.annotate(year=TruncYear('date')).values('year')
    
    for year_data in yearly_data.distinct():
        year = year_data['year'].year
        
        # First half (Jan-Jun)
        h1_sales = sales_qs.filter(date__year=year, date__month__lte=6).aggregate(
            total=Sum('total_sales')
        )['total'] or 0
        
        # Second half (Jul-Dec)
        h2_sales = sales_qs.filter(date__year=year, date__month__gte=7).aggregate(
            total=Sum('total_sales')
        )['total'] or 0
        
        half_yearly_sales.append({
            'year': year,
            'h1': float(h1_sales),
            'h2': float(h2_sales),
            'h1_label': f'H1 {year}',
            'h2_label': f'H2 {year}'
        })
    
    # YEARLY DATA
    yearly_sales = sales_qs.annotate(year=TruncYear('date')).values('year').annotate(
        total=Sum('total_sales')
    ).order_by('year')
    
    yearly_sales_list = list(yearly_sales)
    yearly_labels = [str(x['year'].year) for x in yearly_sales_list]
    yearly_values = [float(x['total'] or 0) for x in yearly_sales_list]
    
    # Year-on-year growth
    yearly_growth = []
    for i in range(len(yearly_values)):
        if i == 0:
            yearly_growth.append(0)
        else:
            prev = yearly_values[i-1]
            curr = yearly_values[i]
            growth = ((curr - prev) / prev * 100) if prev > 0 else 0
            yearly_growth.append(round(growth, 2))
    
    yearly_avg_sales = sum(yearly_values) / len(yearly_values) if yearly_values else 0
    
    # ==================== DAILY TRENDS ====================
    daily_sales = sales_qs.values('date').annotate(
        sales=Sum('total_sales'),
        online=Sum('online_received'),
        cash=Sum('cash_received')
    ).order_by('date')
    
    sales_dates = [x['date'].strftime('%Y-%m-%d') for x in daily_sales]
    sales_values = [float(x['sales'] or 0) for x in daily_sales]
    daily_avg_sales = sum(sales_values) / len(sales_values) if sales_values else 0
    
    daily_expenses = expenses_qs.values('date').annotate(
        expense=Sum('total')
    ).order_by('date')
    
    expense_dates = [x['date'].strftime('%Y-%m-%d') for x in daily_expenses]
    expense_values = [float(x['expense'] or 0) for x in daily_expenses]
    
    # ==================== WEEKDAY PERFORMANCE ====================
    weekday_sales = sales_qs.values('day').annotate(
        avg_sales=Avg('total_sales')
    ).order_by('day')
    
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_dict = {x['day']: float(x['avg_sales'] or 0) for x in weekday_sales}
    weekday_labels = weekday_order
    weekday_values = [weekday_dict.get(day, 0) for day in weekday_order]
    
    # ==================== BEST/WORST PERIODS ====================
    # Auto-detect best and worst performing months
    if monthly_sales_list:
        best_month = max(monthly_sales_list, key=lambda x: x['total'] or 0)
        worst_month = min(monthly_sales_list, key=lambda x: x['total'] or 0)
        
        best_month_info = {
            'period': best_month['month'].strftime('%B %Y'),
            'value': float(best_month['total'] or 0),
            'type': 'Month'
        }
        
        worst_month_info = {
            'period': worst_month['month'].strftime('%B %Y'),
            'value': float(worst_month['total'] or 0),
            'type': 'Month'
        }
    else:
        best_month_info = worst_month_info = None
    
    # ==================== NET CONTRIBUTION ====================
    net_contribution = total_sales - total_labor - total_delivery - total_expense
    
    # Performance color  
    if net_contribution > total_sales * 0.3:
        contribution_color = 'success'
    elif net_contribution > 0:
        contribution_color = 'warning'
    else:
        contribution_color = 'danger'
    
    # ==================== EXPORT HANDLING ====================
    if export_format:
        return handle_analytics_export(
            export_format,
            {
                'sales': monthly_sales_list,
                'expenses': monthly_expense_list,
                'start_date': start_date,
                'end_date': end_date,
                'total_sales': total_sales,
                'total_expense': total_expense,
                'net_contribution': net_contribution
            }
        )
    
    # ==================== CONTEXT ====================
    context = {
        # Filters
        'start_date': start_date,
        'end_date': end_date,
        'month': month,
        'time_view': time_view,
        
        # Basic KPIs
        'total_sales': total_sales,
        'avg_sales': avg_sales,
        'total_online_sales': total_online_sales,
        'total_cash_sales': total_cash_sales,
        'online_pct': online_pct,
        'cash_pct': cash_pct,
        'total_labor': total_labor,
        'total_delivery': total_delivery,
        'total_expense': total_expense,
        'avg_expense': avg_expense,
        'total_online_exp': total_online_exp,
        'total_cash_exp': total_cash_exp,
        'online_exp_pct': online_exp_pct,
        'cash_exp_pct': cash_exp_pct,
        
        # Min/Max Detection
        'min_sale_day': min_sale_day,
        'max_sale_day': max_sale_day,
        'min_expense_day': min_expense_day,
        'max_expense_day': max_expense_day,
        'min_sales_month': min_sales_month,
        'min_sales_month_value': min_sales_month_value,
        'max_sales_month': max_sales_month,
        'max_sales_month_value': max_sales_month_value,
        
        # Averages
        'daily_avg_sales': daily_avg_sales,
        'monthly_avg_sales': monthly_avg_sales,
        'quarterly_avg_sales': quarterly_avg_sales,
        'yearly_avg_sales': yearly_avg_sales,
        'monthly_avg_expense': monthly_avg_expense,
        
        # Growth Rates
        'monthly_growth_json': json.dumps(monthly_growth),
        'quarterly_growth_json': json.dumps(quarterly_growth),
        'yearly_growth_json': json.dumps(yearly_growth),
        
        # Time-based data
        'monthly_sales_labels_json': json.dumps(monthly_sales_labels),
        'monthly_sales_values_json': json.dumps(monthly_sales_values),
        'monthly_expense_labels_json': json.dumps(monthly_expense_labels),
        'monthly_expense_values_json': json.dumps(monthly_expense_values),
        
        'quarterly_labels_json': json.dumps(quarterly_labels),
        'quarterly_values_json': json.dumps(quarterly_values),
        
        'yearly_labels_json': json.dumps(yearly_labels),
        'yearly_values_json': json.dumps(yearly_values),
        
        'half_yearly_sales': half_yearly_sales,
        
        # Daily data
        'sales_dates_json': json.dumps(sales_dates),
        'sales_values_json': json.dumps(sales_values),
        'expense_dates_json': json.dumps(expense_dates),
        'expense_values_json': json.dumps(expense_values),
        
        # Weekday
        'weekday_labels_json': json.dumps(weekday_labels),
        'weekday_values_json': json.dumps(weekday_values),
        
        # Best/Worst
        'best_month_info': best_month_info,
        'worst_month_info': worst_month_info,
        
        # Combined
        'net_contribution': net_contribution,
        'contribution_color': contribution_color,
    }
    
    return render(request, 'admin/admin_analytics.html', context)


def handle_analytics_export(format_type, data):
    """
    Handle export in PDF, Excel, CSV, or PNG format
    """
    if format_type == 'csv':
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Period', 'Sales', 'Expenses', 'Net'])
        
        for i, sale in enumerate(data['sales']):
            expense = data['expenses'][i] if i < len(data['expenses']) else {'total': 0}
            writer.writerow([
                sale['month'].strftime('%Y-%m'),
                sale['total'],
                expense['total'],
                sale['total'] - expense['total']
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{timezone.now().strftime("%Y%m%d")}.csv"'
        return response
    
    elif format_type == 'excel':
        try:
            import openpyxl
            from openpyxl.utils import get_column_letter
            from io import BytesIO
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Analytics Report"
            
            # Headers
            ws['A1'] = 'Analytics Report'
            ws['A2'] = f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M")}'
            ws['A3'] = f'Period: {data["start_date"]} to {data["end_date"]}'
            
            # Data headers
            ws['A5'] = 'Month'
            ws['B5'] = 'Sales'
            ws['C5'] = 'Expenses'
            ws['D5'] = 'Net Contribution'
            
            row = 6
            for i, sale in enumerate(data['sales']):
                expense = data['expenses'][i] if i < len(data['expenses']) else {'total': 0}
                ws[f'A{row}'] = sale['month'].strftime('%B %Y')
                ws[f'B{row}'] = float(sale['total'])
                ws[f'C{row}'] = float(expense['total'])
                ws[f'D{row}'] = float(sale['total']) - float(expense['total'])
                row += 1
            
            # Summary
            ws[f'A{row+1}'] = 'TOTAL'
            ws[f'B{row+1}'] = data['total_sales']
            ws[f'C{row+1}'] = data['total_expense']
            ws[f'D{row+1}'] = data['net_contribution']
            
            output = BytesIO()
            wb.save(output)
            output.seek(0)
            
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="analytics_{timezone.now().strftime("%Y%m%d")}.xlsx"'
            return response
        except ImportError:
            # Fallback to CSV if openpyxl not installed
            return handle_analytics_export('csv', data)
    
    else:
        # Default to CSV
        return handle_analytics_export('csv', data)

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
    # Default: Date DESC (most recent first)
    sort_by = request.GET.get('sort_by', 'date')
    sort_order = request.GET.get('sort_order', 'desc')
    
    # Validate sortable fields
    sortable_fields = ['date', 'day', 'total_sales', 'online_received', 'cash_received', 
                       'labor_charge', 'delivery_charge', 'subtotal', 'admin__username']
    
    if sort_by not in sortable_fields:
        sort_by = 'date'
    
    # Build order_by string
    if sort_order == 'desc':
        order_field = f'-{sort_by}'
    else:
        order_field = sort_by
    
    sales_list = DailySales.objects.all().order_by(order_field)
    
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
    total_labor = sales_list.aggregate(Sum('labor_charge'))['labor_charge__sum'] or 0
    total_delivery = sales_list.aggregate(Sum('delivery_charge'))['delivery_charge__sum'] or 0

    paginator = Paginator(sales_list, 50)  # Show 50 records per page
    page_number = request.GET.get('page')
    sales_records = paginator.get_page(page_number)

    context = {
        'sales_records': sales_records,
        'total_sales': total_sales,
        'total_online': total_online,
        'total_cash': total_cash,
        'total_labor': total_labor,
        'total_delivery': total_delivery,
        'current_sort_by': sort_by,
        'current_sort_order': sort_order,
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
    # Default: Date DESC (most recent first)
    sort_by = request.GET.get('sort_by', 'date')
    sort_order = request.GET.get('sort_order', 'desc')
    
    # Validate sortable fields
    sortable_fields = ['date', 'day', 'online_amount', 'cash_amount', 'total', 'admin__username']
    
    if sort_by not in sortable_fields:
        sort_by = 'date'
    
    # Build order_by string
    if sort_order == 'desc':
        order_field = f'-{sort_by}'
    else:
        order_field = sort_by
    
    expenses_list = DailyExpenditure.objects.all().order_by(order_field, '-created_at')
    
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


    # Calculate Totals (using combined online + cash model)
    total_expenses = expenses_list.aggregate(Sum('total'))['total__sum'] or 0
    total_online_expenses = expenses_list.aggregate(Sum('online_amount'))['online_amount__sum'] or 0
    total_cash_expenses = expenses_list.aggregate(Sum('cash_amount'))['cash_amount__sum'] or 0

    paginator = Paginator(expenses_list, 50)  # Show 50 records per page
    page_number = request.GET.get('page')
    expenses = paginator.get_page(page_number)

    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'total_online_expenses': total_online_expenses,
        'total_cash_expenses': total_cash_expenses,
        'current_sort_by': sort_by,
        'current_sort_order': sort_order,
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
    
    # Define columns - updated to include labor and delivery charges
    columns = ['Date', 'Day', 'Total Sales', 'Online', 'Cash', 'Labor Charge', 'Delivery Charge', 'Subtotal', 'Remark', 'Admin']
    data = []
    for sale in sales:
        data.append([
            str(sale.date), 
            sale.day, 
            str(sale.total_sales), 
            str(sale.online_received), 
            str(sale.cash_received),
            str(sale.labor_charge) if sale.labor_charge is not None else '0.00',
            str(sale.delivery_charge) if sale.delivery_charge is not None else '0.00',
            str(sale.subtotal),
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
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="daily_sales.pdf"'
        
        # Use landscape mode for wider table with more columns
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
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
            ('FONTSIZE', (0, 0), (-1, -1), 6),
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
    
    columns = ['Date', 'Day', 'Online Amount', 'Cash Amount', 'Total', 'Description', 'Admin']
    data = []
    for ex in expenses:
        data.append([
            str(ex.date), 
            ex.day, 
            str(ex.online_amount) if ex.online_amount is not None else '0.00',
            str(ex.cash_amount) if ex.cash_amount is not None else '0.00',
            str(ex.total),
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

            # Required: Date, Online Amount, Cash Amount
            # Mappable column names
            required = ['date']
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
                        online_amount=row.get('online_amount', 0) or 0,
                        cash_amount=row.get('cash_amount', 0) or 0,
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
