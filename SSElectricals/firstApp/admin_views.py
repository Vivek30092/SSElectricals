from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Appointment, AdminActivityLog, AdminSession

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
