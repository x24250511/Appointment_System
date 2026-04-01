from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Appointment, AppointmentHistory
from .services import EmailService, PDFService
from django.db.models import Q, Count


def is_staff(user):
    return user.is_staff or user.is_superuser


@login_required(login_url="/auth/login/")
@user_passes_test(is_staff)
def admin_dashboard_view(request):
    # Get statistics
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    confirmed_appointments = Appointment.objects.filter(
        status='confirmed').count()
    completed_appointments = Appointment.objects.filter(
        status='completed').count()
    cancelled_appointments = Appointment.objects.filter(
        status='cancelled').count()

    # Recent appointments
    recent_appointments = Appointment.objects.all().order_by(
        '-created_at')[:10]

    # Appointments by industry
    industry_stats = Appointment.objects.values(
        'industry').annotate(count=Count('id'))

    context = {
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'recent_appointments': recent_appointments,
        'industry_stats': industry_stats,
    }

    return render(request, 'appointments/admin_dashboard.html', context)


@login_required(login_url="/auth/login/")
@user_passes_test(is_staff)
def admin_appointments_view(request):
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    industry_filter = request.GET.get('industry', 'all')
    search_query = request.GET.get('search', '')

    appointments = Appointment.objects.all().order_by('-created_at')

    # Apply filters
    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)

    if industry_filter != 'all':
        appointments = appointments.filter(industry=industry_filter)

    if search_query:
        appointments = appointments.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    context = {
        'appointments': appointments,
        'status_filter': status_filter,
        'industry_filter': industry_filter,
        'search_query': search_query,
    }

    return render(request, 'appointments/admin_appointments.html', context)


@login_required(login_url="/auth/login/")
@user_passes_test(is_staff)
def admin_appointment_detail_view(request, appointment_id):
    """Admin view for single appointment with actions"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    history = AppointmentHistory.objects.filter(
        appointment=appointment).order_by('-timestamp')

    context = {
        'appointment': appointment,
        'history': history,
    }

    return render(request, 'appointments/admin_appointment_detail.html', context)


@login_required(login_url="/auth/login/")
@user_passes_test(is_staff)
def admin_confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.status != 'confirmed':
        appointment.status = 'confirmed'
        appointment.save()

        # Create history record
        AppointmentHistory.objects.create(
            appointment=appointment,
            action='confirmed',
            performed_by=request.user,
            notes='Appointment confirmed by admin'
        )

        # Generate PDF
        pdf_data = None
        try:
            pdf_result = PDFService.generate_appointment_pdf(appointment)
            if pdf_result.get('success'):
                appointment.pdf_generated = True
                pdf_data = pdf_result.get('pdf_data')
                appointment.save()
                print(
                    f"[PDF] Successfully generated for appointment {appointment.id}")
        except Exception as e:
            print(f"PDF generation failed: {str(e)}")

        # Send confirmation email with PDF attachment
        try:
            subject = f" Appointment Confirmed: {appointment.title}"
            body = f"""Dear {appointment.user.username},

Good news! Your appointment has been confirmed by our team.

Appointment Details:
Title: {appointment.title}
Industry: {appointment.get_industry_display()}
Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Location: {appointment.location}

Description:
{appointment.description}

Please arrive 10 minutes early for your appointment.

If you need to reschedule or cancel, please contact us as soon as possible.

Best regards,
SecureFlow Team
"""

            # Send with or without PDF attachment
            if pdf_data:
                result = EmailService.send_email_with_attachment(
                    appointment.user.email,
                    subject,
                    body,
                    pdf_data,
                    f'appointment_{appointment.id}.pdf',
                    from_name="SecureFlow Appointments"
                )
            else:
                result = EmailService.send_email(
                    appointment.user.email,
                    subject,
                    body,
                    from_name="SecureFlow Appointments"
                )

            appointment.email_sent = True
            appointment.save()
            messages.success(
                request, f'Appointment confirmed and email sent to {appointment.user.email}')
        except Exception as e:
            messages.warning(
                request, f'Appointment confirmed but email failed: {str(e)}')
    else:
        messages.info(request, 'Appointment is already confirmed.')

    return redirect('admin_appointment_detail', appointment_id=appointment_id)


@login_required(login_url="/auth/login/")
@user_passes_test(is_staff)
# Mark appointment as completed
def admin_complete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    appointment.status = 'completed'
    appointment.save()

    # Create history record
    AppointmentHistory.objects.create(
        appointment=appointment,
        action='completed',
        performed_by=request.user,
        notes='Appointment marked as completed by admin'
    )

    messages.success(request, 'Appointment marked as completed.')
    return redirect('admin_appointment_detail', appointment_id=appointment_id)


@login_required(login_url="/auth/login/")
@user_passes_test(is_staff)
def admin_cancel_appointment(request, appointment_id):
    """Cancel appointment and notify user"""
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.status != 'cancelled':
        appointment.status = 'cancelled'
        appointment.save()

        # Create history record
        AppointmentHistory.objects.create(
            appointment=appointment,
            action='cancelled',
            performed_by=request.user,
            notes='Appointment cancelled by admin'
        )

        # Send cancellation email
        try:
            subject = f" Appointment Cancelled: {appointment.title}"
            body = f"""Dear {appointment.user.username},

We regret to inform you that your appointment has been cancelled.

Cancelled Appointment:
Title: {appointment.title}
Date: {appointment.appointment_date.strftime('%B %d, %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Location: {appointment.location}

If you would like to reschedule, please create a new appointment through our system.

We apologize for any inconvenience.

Best regards,
SecureFlow Team
"""
            EmailService.send_email(
                appointment.user.email, subject, body, from_name="SecureFlow Appointments")
            messages.success(
                request, f'Appointment cancelled and email sent to {appointment.user.email}')
        except Exception as e:
            messages.warning(
                request, f'Appointment cancelled but email failed: {str(e)}')
    else:
        messages.info(request, 'Appointment is already cancelled.')

    return redirect('admin_appointment_detail', appointment_id=appointment_id)
