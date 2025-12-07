import pandas as pd
import os
from django.conf import settings
from .models import Order

def export_orders_to_excel():
    """Export confirmed orders to Excel for analysis."""
    file_path = os.path.join(settings.MEDIA_ROOT, 'data', 'orders_analytics.xlsx')
    
    # Filter only confirmed orders (Confirmed, Out for Delivery, Delivered)
    orders = Order.objects.filter(status__in=['Confirmed', 'Out for Delivery', 'Delivered'])
    
    data = []
    for order in orders:
        # Get items string
        items_str = ", ".join([f"{item.product.name} ({item.quantity})" for item in order.items.all()])
        
        # We need individual rows for product analysis if we want granule data, 
        # but for an 'orders' sheet, one row per order.
        # Let's start with one row per order for easy reading.
        # Actually, for Product Analysis ("Most purchased products"), we might need a separate dataframe or exploded view.
        # For simplicity, let's dump Order-level data and maybe a secondary sheet for Items if needed. 
        # But pandas can handle JSON-like item strings if we parse, or we can just iterate items differently.
        
        # Better approach: Flat table with Order details repeated for each Item (Standard transactional data)
        for item in order.items.all():
            data.append({
                'Order ID': order.id,
                'Date': order.created_at.date(),
                'Month': order.created_at.strftime('%Y-%m'),
                'Customer': order.user.username,
                'Product': item.product.name,
                'Category': item.product.category.name if item.product.category else 'Uncategorized',
                'Quantity': item.quantity,
                'Unit Price': float(item.price),
                'Item Total': float(item.total_price),
                'Order Total Revenue': float(order.final_price) if order.final_price else 0.0, # Note: This duplicates the revenue per row, need care in aggregation
                'Delivery Charge': float(order.delivery_charge),
                'Distance (KM)': float(order.distance_km),
                'Status': order.status
            })
            
    if not data:
        return None, "No confirmed orders found to export."
        
    df = pd.DataFrame(data)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        df.to_excel(file_path, index=False)
        return file_path, None
    except Exception as e:
        return None, str(e)

def analyze_orders_data():
    """Read .xlsx and perform analysis."""
    file_path = os.path.join(settings.MEDIA_ROOT, 'data', 'orders_analytics.xlsx')
    
    if not os.path.exists(file_path):
        return None, "Data file not found. Please refresh data first."
    
    try:
        df = pd.read_excel(file_path)
        
        if df.empty:
            return None, "The data file is empty."
            
        stats = {}
        
        # 1. Total Orders (Unique IDs)
        stats['total_orders'] = df['Order ID'].nunique()
        
        # 2. Total Revenue
        # Since 'Order Total Revenue' is repeated for each item in an order, we must take unique orders to sum revenue using 'Order ID' and 'Order Total Revenue'?
        # A safer way if we have item level data: Sum of 'Item Total' + Unique 'Delivery Charge' per order? 
        # Or just take the 'Order Total Revenue' of unique order rows.
        unique_orders = df.drop_duplicates(subset=['Order ID'])
        stats['total_revenue'] = unique_orders['Order Total Revenue'].sum()
        stats['total_delivery_charges'] = unique_orders['Delivery Charge'].sum()
        stats['avg_distance'] = round(unique_orders['Distance (KM)'].mean(), 2)
        
        # 3. Product Analysis (Group by Product)
        product_groups = df.groupby('Product')['Quantity'].sum().sort_values(ascending=False).head(10)
        stats['top_products_html'] = product_groups.to_frame().to_html(classes="table table-striped table-hover", border=0)
        
        # 4. Monthly Revenue
        monthly_groups = unique_orders.groupby('Month')['Order Total Revenue'].sum()
        stats['monthly_revenue_html'] = monthly_groups.to_frame().to_html(classes="table table-striped table-hover", border=0, formatters={'Order Total Revenue': '₹{:,.2f}'.format})
        
        # Format currency for display
        stats['total_revenue'] = "{:,.2f}".format(stats['total_revenue'])
        stats['total_delivery_charges'] = "{:,.2f}".format(stats['total_delivery_charges'])
        
        return stats, None
        
    except Exception as e:
        return None, f"Error analyzing data: {str(e)}"
