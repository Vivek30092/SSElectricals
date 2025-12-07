from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Appointment, AdminActivityLog, AdminSession, Order
import os
from django.conf import settings
import pandas as pd


@staff_member_required
def admin_dashboard(request):
    return render(request, 'admin/admin_dashboard.html')

@staff_member_required
def admin_activity_log_view(request):
    logs = AdminActivityLog.objects.all()
    return render(request, 'admin/admin_activity_log.html', {'logs': logs})

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
