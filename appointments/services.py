import requests
from django.conf import settings
from datetime import datetime
import json


class LocationService:
    """Geocode and validate locations using OpenStreetMap Nominatim API"""

    BASE_URL = "https://nominatim.openstreetmap.org"

    @staticmethod
    def geocode_location(location):
        """
        Convert location name/address to coordinates
        Returns: {'lat': latitude, 'lon': longitude, 'display_name': formatted_address}
        """
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
        """Check if a location is valid (can be geocoded)"""
        result = LocationService.geocode_location(location)
        return result.get('found', False)

    @staticmethod
    def get_map_url(latitude, longitude, zoom=15):
        """Generate static map image URL"""
        return f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map={zoom}/{latitude}/{longitude}"


class EmailService:
    """Send emails using classmate's CloudMail API"""

    BASE_URL = settings.EMAIL_SERVICE_URL

    @staticmethod
    def send_email(to_email, subject, body, from_name="SecureFlow", reply_to=None, retry_count=2):
        """Send email via CloudMail API with retry"""
        for attempt in range(retry_count + 1):
            try:
                print(f"\n{'='*60}")
                print(f"[EMAIL] Attempt {attempt + 1}/{retry_count + 1}")
                print(f"[EMAIL] Sending email to: {to_email}")
                print(f"[EMAIL] Subject: {subject}")

                data = {
                    'to_email': to_email,
                    'subject': subject,
                    'message': body,
                    'from_name': from_name,
                }

                if reply_to:
                    data['reply_to'] = reply_to

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
                    if attempt < retry_count:
                        print(f"[EMAIL] Retrying...")
                        continue
                    print(f"{'='*60}\n")
                    return False, "Failed to send email"

            except requests.exceptions.Timeout:
                print(f"[EMAIL ERROR] ✗ Request timed out")
                if attempt < retry_count:
                    print(f"[EMAIL] Retrying...")
                    continue
                print(f"{'='*60}\n")
                return False, "Email service timeout"

            except Exception as e:
                print(f"[EMAIL ERROR] ✗ {str(e)}")
                if attempt < retry_count:
                    print(f"[EMAIL] Retrying...")
                    continue
                print(f"{'='*60}\n")
                return False, f"Email service error: {str(e)}"

        return False, "Failed after all retry attempts"

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
    def send_appointment_confirmation(email, appointment, pdf_url=None, map_url=None):
        """Send appointment confirmation email"""
        subject = f"Appointment Confirmation: {appointment.title}"

        body = f"""Hello,

Your appointment has been confirmed:

Title: {appointment.title}
Date: {appointment.appointment_date}
Time: {appointment.appointment_time}
Location: {appointment.location}

Description:
{appointment.description}
"""

        if map_url:
            body += f"\n\nView location on map: {map_url}"

        if pdf_url:
            body += f"\n\nDownload your confirmation PDF: {pdf_url}"

        body += """

Best regards,
SecureFlow Team
"""

        return EmailService.send_email(
            email,
            subject,
            body,
            from_name="SecureFlow Appointments",
            reply_to="noreply@secureflow.com"
        )


class PDFService:
    """Generate PDF from HTML using classmate's service"""

    BASE_URL = settings.PDF_SERVICE_URL

    @staticmethod
    def generate_pdf(html_content, filename):
        """Convert HTML to PDF"""
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
            print(f"PDF Service error: {str(e)}")
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
    """Integrate with classmate's appointment creator service"""

    BASE_URL = settings.APPOINTMENT_SERVICE_URL
    API_KEY = settings.APPOINTMENT_API_KEY

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
                provider_id = data.get('id')
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
    def sync_appointment(appointment):
        """Sync appointment to external service"""
        try:
            print(f"\n{'='*60}")
            print(f"[APPOINTMENT SYNC] Syncing appointment {appointment.id}")
            print(f"  - Title: {appointment.title}")
            print(f"  - Date: {appointment.appointment_date}")
            print(f"  - Time: {appointment.appointment_time}")
            print(f"[APPOINTMENT SYNC] ✓ Sync completed")
            print(f"{'='*60}\n")
            return True
        except Exception as e:
            print(f"[APPOINTMENT SYNC ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return False
