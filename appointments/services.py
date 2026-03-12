import requests
from django.conf import settings
from datetime import datetime
import json


class LocationService:
    """Geocode and validate locations using OpenStreetMap Nominatim API"""

    BASE_URL = "https://nominatim.openstreetmap.org"

    @staticmethod
    def geocode_location(location):
        """Convert location name/address to coordinates"""
        try:
            print(f"\n{'='*60}")
            print(f"[MAPS API] Geocoding location: {location}")

            response = requests.get(
                f"{LocationService.BASE_URL}/search",
                params={
                    'q': location,
                    'format': 'json',
                    'limit': 1
                },
                headers={
                    'User-Agent': 'SecureFlow-AppointmentSystem/1.0'
                },
                timeout=10
            )

            print(f"[MAPS API] Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if data:
                    result = data[0]
                    location_data = {
                        'latitude': float(result['lat']),
                        'longitude': float(result['lon']),
                        'display_name': result['display_name'],
                        'found': True
                    }
                    print(
                        f"[MAPS API] ✓ Location found: {result['display_name']}")
                    print(
                        f"[MAPS API] Coordinates: ({location_data['latitude']}, {location_data['longitude']})")
                    print(f"{'='*60}\n")
                    return location_data
                else:
                    print(f"[MAPS API] ✗ Location not found")
                    print(f"{'='*60}\n")
                    return {'found': False}
            else:
                print(f"[MAPS API] ✗ Failed: {response.text}")
                print(f"{'='*60}\n")
                return {'found': False}

        except Exception as e:
            print(f"[MAPS API ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return {'found': False}

    @staticmethod
    def validate_location(location):
        """Check if a location is valid"""
        result = LocationService.geocode_location(location)
        return result.get('found', False)

    @staticmethod
    def get_map_url(latitude, longitude, zoom=15):
        """Generate map URL"""
        return f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map={zoom}/{latitude}/{longitude}"


class EmailService:
    """Send emails using CloudMail API"""

    BASE_URL = settings.EMAIL_SERVICE_URL

    @staticmethod
    def send_email(to_email, subject, body, from_name="SecureFlow"):
        """Send email via CloudMail API"""
        try:
            print(f"\n{'='*60}")
            print(f"[EMAIL] Sending to: {to_email}")
            print(f"[EMAIL] Subject: {subject}")

            data = {
                'to_email': to_email,
                'subject': subject,
                'message': body,
                'from_name': from_name,
            }

            response = requests.post(
                f"{EmailService.BASE_URL}/api/send/",
                data=data,
                timeout=30
            )

            print(f"[EMAIL] Response Status: {response.status_code}")

            if response.status_code == 200:
                print(f"[EMAIL] ✓ Email sent successfully")
                print(f"{'='*60}\n")
                return True, "Email sent successfully"
            else:
                print(f"[EMAIL] ✗ Failed: {response.text}")
                print(f"{'='*60}\n")
                return False, "Failed to send email"

        except Exception as e:
            print(f"[EMAIL ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return False, f"Email service error: {str(e)}"

    @staticmethod
    def send_otp_email(email, otp_code):
        """Send OTP via email"""
        subject = "Your OTP Code - SecureFlow"
        body = f"""Hello,

Your OTP code is: {otp_code}

This code is valid for 5 minutes.

If you didn't request this code, please ignore this email.

Best regards,
SecureFlow Team
"""
        return EmailService.send_email(email, subject, body, from_name="SecureFlow Authentication")

    @staticmethod
    def send_appointment_confirmation(email, appointment, map_url=None):
        """Send appointment confirmation email"""
        subject = f"Appointment Confirmation: {appointment.title}"

        body = f"""Hello,

Your appointment has been confirmed:

Title: {appointment.title}
Industry: {appointment.get_industry_display()}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}
Location: {appointment.location}

Description:
{appointment.description}
"""

        if map_url:
            body += f"\n\nView location on map: {map_url}"

        body += """

Best regards,
SecureFlow Team
"""

        return EmailService.send_email(email, subject, body, from_name="SecureFlow Appointments")


class PDFService:
    """Generate PDF from HTML"""

    BASE_URL = settings.PDF_SERVICE_URL

    @staticmethod
    def generate_pdf(html_content, filename):
        """Convert HTML to PDF (placeholder - service offline)"""
        try:
            response = requests.post(
                f"{PDFService.BASE_URL}/generate",
                json={
                    'html': html_content,
                    'filename': filename
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('pdf_url')
        except Exception as e:
            print(f"[PDF Service] Service unavailable: {str(e)}")
            return None

    @staticmethod
    def create_appointment_html(appointment, location_data=None):
        """Create HTML template for appointment"""
        location_info = ""
        if location_data and location_data.get('found'):
            location_info = f"""
                <div class="detail">
                    <span class="label">Coordinates:</span> {location_data['latitude']}, {location_data['longitude']}
                </div>
                <div class="detail">
                    <span class="label">Full Address:</span> {location_data['display_name']}
                </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ margin: 20px 0; }}
                .detail {{ margin: 10px 0; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Appointment Confirmation</h1>
            </div>
            <div class="content">
                <div class="detail">
                    <span class="label">Appointment ID:</span> {appointment.id}
                </div>
                <div class="detail">
                    <span class="label">Industry:</span> {appointment.get_industry_display()}
                </div>
                <div class="detail">
                    <span class="label">Title:</span> {appointment.title}
                </div>
                <div class="detail">
                    <span class="label">Description:</span> {appointment.description}
                </div>
                <div class="detail">
                    <span class="label">Date:</span> {appointment.appointment_date}
                </div>
                <div class="detail">
                    <span class="label">Time:</span> {appointment.appointment_time}
                </div>
                <div class="detail">
                    <span class="label">Location:</span> {appointment.location}
                </div>
                {location_info}
                <div class="detail">
                    <span class="label">Status:</span> {appointment.get_status_display()}
                </div>
            </div>
        </body>
        </html>
        """
        return html


class AppointmentCreatorService:
    """Integrate with Appointment Creator API - Full Dynamic Slot Management"""

    BASE_URL = settings.APPOINTMENT_SERVICE_URL
    API_KEY = getattr(settings, 'APPOINTMENT_API_KEY', '')

    @staticmethod
    def create_provider(name):
        """Create a service provider in external system"""
        try:
            print(f"\n{'='*60}")
            print(f"[APPOINTMENT API] Creating provider: {name}")

            response = requests.post(
                f"{AppointmentCreatorService.BASE_URL}/providers/",
                headers={
                    'X-API-KEY': AppointmentCreatorService.API_KEY,
                    'Content-Type': 'application/json'
                },
                json={'name': name},
                timeout=10
            )

            print(f"[APPOINTMENT API] Response Status: {response.status_code}")

            if response.status_code in [200, 201]:
                data = response.json()
                provider_id = data.get('provider_id')
                print(
                    f"[APPOINTMENT API] ✓ Provider created with ID: {provider_id}")
                print(f"{'='*60}\n")
                return provider_id
            else:
                print(f"[APPOINTMENT API] ✗ Failed: {response.text}")
                print(f"{'='*60}\n")
                return None

        except Exception as e:
            print(f"[APPOINTMENT API ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return None

    @staticmethod
    def get_provider_id_for_industry(industry):
        """Get provider ID based on industry"""
        from django.conf import settings

        provider_map = {
            'healthcare': settings.HEALTHCARE_PROVIDER_ID,
            'legal': settings.LEGAL_PROVIDER_ID,
            'consultancy': settings.CONSULTANCY_PROVIDER_ID,
        }

        return provider_map.get(industry)

    @staticmethod
    def generate_slots_for_date(provider_id, date):
        """Generate 30-minute slots from 9 AM to 6 PM"""
        try:
            print(f"\n{'='*60}")
            print(
                f"[APPOINTMENT API] Generating slots for provider {provider_id} on {date}")

            response = requests.post(
                f"{AppointmentCreatorService.BASE_URL}/api/generate-slots/",
                headers={
                    'X-API-KEY': AppointmentCreatorService.API_KEY,
                    'Content-Type': 'application/json'
                },
                json={
                    'provider_id': int(provider_id),
                    'date': date,
                    'start_time': '09:00',
                    'end_time': '18:00'
                },
                timeout=10
            )

            print(f"[APPOINTMENT API] Response Status: {response.status_code}")

            if response.status_code in [200, 201]:
                data = response.json()
                print(
                    f"[APPOINTMENT API] ✓ {data.get('message', 'Slots generated')}")
                print(f"{'='*60}\n")
                return True
            else:
                print(f"[APPOINTMENT API] Response: {response.text}")
                print(f"{'='*60}\n")
                return False

        except Exception as e:
            print(f"[APPOINTMENT API ERROR] {str(e)}")
            print(f"{'='*60}\n")
            return False

    @staticmethod
    def get_available_slots(provider_id, date):
        """Get available slots for a provider on a specific date"""
        try:
            print(f"\n{'='*60}")
            print(
                f"[APPOINTMENT API] Getting slots for provider {provider_id} on {date}")

            response = requests.get(
                f"{AppointmentCreatorService.BASE_URL}/slots/",
                headers={
                    'X-API-KEY': AppointmentCreatorService.API_KEY,
                },
                params={
                    'provider_id': provider_id,
                    'date': date
                },
                timeout=10
            )

            print(f"[APPOINTMENT API] Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                slots = data.get('slots', [])
                print(
                    f"[APPOINTMENT API] ✓ Found {len(slots)} available slots")
                print(f"{'='*60}\n")
                return slots
            else:
                print(f"[APPOINTMENT API] ✗ Failed: {response.text}")
                print(f"{'='*60}\n")
                return []

        except Exception as e:
            print(f"[APPOINTMENT API ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return []

    @staticmethod
    def book_slot(slot_id, customer_name, customer_email):
        """Book a specific slot"""
        try:
            print(f"\n{'='*60}")
            print(f"[APPOINTMENT API] Booking slot {slot_id}")

            response = requests.post(
                f"{AppointmentCreatorService.BASE_URL}/book/",
                headers={
                    'X-API-KEY': AppointmentCreatorService.API_KEY,
                    'Content-Type': 'application/json'
                },
                json={
                    'slot_id': slot_id,
                    'customer_name': customer_name,
                    'customer_email': customer_email
                },
                timeout=10
            )

            print(f"[APPOINTMENT API] Response Status: {response.status_code}")

            if response.status_code in [200, 201]:
                data = response.json()
                print(f"[APPOINTMENT API] ✓ Slot booked successfully")
                print(f"{'='*60}\n")
                return True, data
            else:
                print(f"[APPOINTMENT API] ✗ Failed: {response.text}")
                print(f"{'='*60}\n")
                return False, None

        except Exception as e:
            print(f"[APPOINTMENT API ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return False, None

    @staticmethod
    def sync_appointment(appointment):
        """Sync appointment to external service with actual slot booking"""
        try:
            if not AppointmentCreatorService.API_KEY:
                print(f"[APPOINTMENT SYNC] External API not configured")
                return False

            print(f"\n{'='*60}")
            print(f"[APPOINTMENT SYNC] Syncing appointment {appointment.id}")

            # Get provider ID for industry
            provider_id = AppointmentCreatorService.get_provider_id_for_industry(
                appointment.industry)

            if not provider_id:
                print(
                    f"[APPOINTMENT SYNC] No provider configured for {appointment.industry}")
                print(f"{'='*60}\n")
                return False

            # Generate slots for the date (if not already generated)
            AppointmentCreatorService.generate_slots_for_date(
                provider_id,
                appointment.appointment_date.strftime('%Y-%m-%d')
            )

            # Get available slots
            slots = AppointmentCreatorService.get_available_slots(
                provider_id,
                appointment.appointment_date.strftime('%Y-%m-%d')
            )

            if not slots:
                print(f"[APPOINTMENT SYNC] No slots available")
                print(f"{'='*60}\n")
                return False

            # Find matching slot for the appointment time
            appointment_time_str = appointment.appointment_time.strftime(
                '%H:%M')
            matching_slot = None

            for slot in slots:
                slot_time = slot.get('time', '')[:5]  # Get HH:MM from HH:MM:SS
                if slot_time == appointment_time_str:
                    matching_slot = slot
                    break

            if matching_slot:
                # Book the slot
                success, booking_data = AppointmentCreatorService.book_slot(
                    matching_slot.get('slot_id'),
                    appointment.user.get_full_name() or appointment.user.username,
                    appointment.user.email
                )

                if success:
                    print(
                        f"[APPOINTMENT SYNC] ✓ Appointment synced and slot booked")
                    print(f"{'='*60}\n")
                    return True

            print(
                f"[APPOINTMENT SYNC] No matching slot found for {appointment_time_str}")
            print(f"{'='*60}\n")
            return False

        except Exception as e:
            print(f"[APPOINTMENT SYNC ERROR] {str(e)}")
            print(f"{'='*60}\n")
            return False
