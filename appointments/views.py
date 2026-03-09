from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Appointment, AppointmentHistory
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentHistorySerializer
)
from .services import LocationService, PDFService, EmailService, AppointmentCreatorService


# ==================== FRONTEND VIEWS ====================

@login_required
def dashboard_view(request):
    """Dashboard page - Server-side rendering"""
    appointments = Appointment.objects.filter(user=request.user)

    # Calculate statistics
    stats = {
        'total': appointments.count(),
        'pending': appointments.filter(status='pending').count(),
        'confirmed': appointments.filter(status='confirmed').count(),
        'cancelled': appointments.filter(status='cancelled').count(),
        'completed': appointments.filter(status='completed').count(),
    }

    # Get recent appointments (last 5)
    recent_appointments = appointments.order_by('-created_at')[:5]

    return render(request, 'appointments/dashboard.html', {
        'stats': stats,
        'recent_appointments': recent_appointments
    })


@login_required
def appointment_list_view(request):
    """List all user's appointments"""
    appointments = Appointment.objects.filter(user=request.user).order_by(
        '-appointment_date', '-appointment_time')

    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments
    })


@login_required
def appointment_create_view(request):
    """Create appointment page"""
    if request.method == 'POST':
        industry = request.POST.get('industry')
        title = request.POST.get('title')
        description = request.POST.get('description')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        location = request.POST.get('location')

        # Validate location
        location_data = LocationService.geocode_location(location)
        if not location_data.get('found'):
            messages.warning(
                request, 'Location not found in maps. Appointment created but location may be invalid.')

        # Create appointment (status defaults to 'pending')
        appointment = Appointment.objects.create(
            user=request.user,
            industry=industry,
            title=title,
            description=description,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            location=location
        )

        # Create history record
        AppointmentHistory.objects.create(
            appointment=appointment,
            action='created',
            performed_by=request.user,
            notes=f'{industry.title()} appointment created - awaiting provider confirmation'
        )

        # Optional: Sync with external appointment service
        try:
            AppointmentCreatorService.sync_appointment(appointment)
        except Exception as e:
            print(f"External sync failed: {e}")

        messages.success(
            request, f'{industry.title()} appointment created! Waiting for provider confirmation.')
        return redirect('appointment_list')

    return render(request, 'appointments/appointment_create.html')


@login_required
def appointment_detail_view(request, appointment_id):
    """View single appointment details"""
    try:
        appointment = Appointment.objects.get(
            id=appointment_id, user=request.user)

        # Get location data
        location_data = LocationService.geocode_location(appointment.location)

        # Get map URL if location found
        map_url = None
        if location_data.get('found'):
            map_url = LocationService.get_map_url(
                location_data['latitude'],
                location_data['longitude']
            )

        return render(request, 'appointments/appointment_detail.html', {
            'appointment': appointment,
            'location_data': location_data,
            'map_url': map_url
        })
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found')
        return redirect('appointment_list')


@login_required
def appointment_edit_view(request, appointment_id):
    """Edit appointment page"""
    try:
        appointment = Appointment.objects.get(
            id=appointment_id, user=request.user)

        if request.method == 'POST':
            # Update appointment
            appointment.industry = request.POST.get('industry')
            appointment.title = request.POST.get('title')
            appointment.description = request.POST.get('description')
            appointment.appointment_date = request.POST.get('appointment_date')
            appointment.appointment_time = request.POST.get('appointment_time')
            appointment.location = request.POST.get('location')
            appointment.save()

            # Create history record
            AppointmentHistory.objects.create(
                appointment=appointment,
                action='updated',
                performed_by=request.user,
                notes='Appointment details updated by user'
            )

            messages.success(request, 'Appointment updated successfully!')
            return redirect('appointment_detail_view', appointment_id=appointment.id)

        return render(request, 'appointments/appointment_edit.html', {
            'appointment': appointment
        })
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found')
        return redirect('appointment_list')


@login_required
def appointment_delete_view(request, appointment_id):
    """Delete appointment"""
    try:
        appointment = Appointment.objects.get(
            id=appointment_id, user=request.user)

        if request.method == 'POST':
            appointment_title = appointment.title
            appointment.delete()
            messages.success(
                request, f'Appointment "{appointment_title}" deleted successfully!')
            return redirect('appointment_list')

        return render(request, 'appointments/appointment_delete.html', {
            'appointment': appointment
        })
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found')
        return redirect('appointment_list')


@login_required
def appointment_change_status(request, appointment_id):
    """
    Change appointment status
    USERS can only CANCEL their appointments
    ADMIN must confirm/complete via admin panel
    """
    try:
        appointment = Appointment.objects.get(
            id=appointment_id, user=request.user)

        if request.method == 'POST':
            new_status = request.POST.get('status')

            # Users can ONLY cancel their own appointments
            if new_status == 'cancelled':
                old_status = appointment.get_status_display()
                appointment.status = 'cancelled'
                appointment.save()

                # Create history record
                AppointmentHistory.objects.create(
                    appointment=appointment,
                    action='cancelled',
                    performed_by=request.user,
                    notes=f'Appointment cancelled by user (was {old_status})'
                )

                messages.success(
                    request, 'Appointment cancelled successfully.')
            else:
                messages.error(
                    request, 'Only cancellation is allowed. Status confirmation must be done by admin/provider.')

        return redirect('appointment_detail_view', appointment_id=appointment.id)

    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found')
        return redirect('appointment_list')


# ==================== API VIEWS ====================

@api_view(['GET', 'POST'])
def appointment_list_create(request):
    """
    GET: List all appointments for authenticated user
    POST: Create new appointment
    """
    if request.method == 'GET':
        appointments = Appointment.objects.filter(user=request.user)
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = AppointmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            appointment = serializer.save(user=request.user)

            # Create history record
            AppointmentHistory.objects.create(
                appointment=appointment,
                action='created',
                performed_by=request.user,
                notes='Appointment created via API'
            )

            # Get location data
            location_data = LocationService.geocode_location(
                appointment.location)

            return Response(
                AppointmentSerializer(appointment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def appointment_detail(request, pk):
    """
    GET: Retrieve appointment details
    PUT: Update appointment
    DELETE: Delete appointment
    """
    try:
        appointment = Appointment.objects.get(pk=pk, user=request.user)
    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AppointmentUpdateSerializer(
            appointment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # Create history record
            AppointmentHistory.objects.create(
                appointment=appointment,
                action='updated',
                performed_by=request.user,
                notes='Appointment updated via API'
            )

            return Response(AppointmentSerializer(appointment).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        appointment.delete()
        return Response(
            {'message': 'Appointment deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


@api_view(['GET'])
def appointment_history(request, pk):
    """Get appointment history/audit trail"""
    try:
        appointment = Appointment.objects.get(pk=pk, user=request.user)
        history = AppointmentHistory.objects.filter(
            appointment=appointment).order_by('-timestamp')
        serializer = AppointmentHistorySerializer(history, many=True)
        return Response(serializer.data)
    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def generate_appointment_pdf(request, pk):
    """Generate PDF for appointment"""
    try:
        appointment = Appointment.objects.get(pk=pk, user=request.user)

        # Get location data
        location_data = LocationService.geocode_location(appointment.location)

        # Create HTML content
        html_content = PDFService.create_appointment_html(
            appointment, location_data)

        # Generate PDF
        pdf_url = PDFService.generate_pdf(
            html_content,
            f"appointment_{appointment.id}.pdf"
        )

        if pdf_url:
            appointment.pdf_generated = True
            appointment.save()

            return Response({
                'message': 'PDF generated successfully',
                'pdf_url': pdf_url
            })
        else:
            return Response(
                {'error': 'Failed to generate PDF'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def send_appointment_email(request, pk):
    """Send appointment confirmation email"""
    try:
        appointment = Appointment.objects.get(pk=pk, user=request.user)

        # Get location data and map URL
        location_data = LocationService.geocode_location(appointment.location)
        map_url = None
        if location_data.get('found'):
            map_url = LocationService.get_map_url(
                location_data['latitude'],
                location_data['longitude']
            )

        # Send email
        success, message = EmailService.send_appointment_confirmation(
            request.user.email,
            appointment,
            pdf_url=None,
            map_url=map_url
        )

        if success:
            appointment.email_sent = True
            appointment.save()

            return Response({
                'message': 'Email sent successfully'
            })
        else:
            return Response(
                {'error': message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def dashboard_stats(request):
    """Get dashboard statistics"""
    appointments = Appointment.objects.filter(user=request.user)

    stats = {
        'total': appointments.count(),
        'pending': appointments.filter(status='pending').count(),
        'confirmed': appointments.filter(status='confirmed').count(),
        'cancelled': appointments.filter(status='cancelled').count(),
        'completed': appointments.filter(status='completed').count(),
    }

    return Response(stats)
