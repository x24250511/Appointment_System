import email

import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import OTPVerification


class OTPService:
    """Service to interact with OTP microservice"""

    BASE_URL = settings.OTP_SERVICE_URL

    @staticmethod
    def generate_otp(email):
        # """Generate OTP using external microservice"""
        try:
            # ALWAYS delete old OTP records for this email first
            deleted_count = OTPVerification.objects.filter(
                email=email).delete()[0]
            if deleted_count > 0:
                print(
                    f"[OTP] Cleaned up {deleted_count} old OTP record(s) for {email}")

            print(f"\n{'='*60}")
            print(f"[OTP] Generating OTP for: {email}")
            print(f"[OTP] Calling API: {OTPService.BASE_URL}/generate-otp")

            response = requests.post(
                f"{OTPService.BASE_URL}/generate-otp",
                json={"key": email},
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            print(f"[OTP] Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                otp_code = data.get('otp')
                expires_in = data.get('expires_in_seconds', 300)

                print(f"[OTP] ✓ OTP Generated Successfully: {otp_code}")
                print(f"[OTP] Expires in: {expires_in} seconds")
                print(f"{'='*60}\n")

                # Store in database with timezone-aware datetime
                OTPVerification.objects.create(
                    email=email,
                    otp_code=otp_code,
                    expires_at=timezone.now() + timedelta(seconds=expires_in)
                )

                return otp_code, expires_in
            else:
                print(f"[OTP] ✗ API returned error: {response.text}")
                print(f"{'='*60}\n")
                return None, None

        except Exception as e:
            print(f"[OTP ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return None, None

    @staticmethod
    def verify_otp(email, otp_code):
        """Verify OTP using external microservice"""
        try:
            print(f"\n{'='*60}")
            print(f"[OTP] Verifying OTP for: {email}")
            print(f"[OTP] OTP Code: {otp_code}")
            print(f"[OTP] Calling API: {OTPService.BASE_URL}/verify-otp")

            response = requests.post(
                f"{OTPService.BASE_URL}/verify-otp",
                json={"key": email, "otp": otp_code},
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            print(f"[OTP] Response Status: {response.status_code}")

            if response.status_code == 200:
                print(f"[OTP] ✓ OTP Verified Successfully")
                print(f"{'='*60}\n")

                # Mark as verified in database
                OTPVerification.objects.filter(
                    email=email,
                    otp_code=otp_code
                ).update(is_verified=True)

                return True, "OTP verified successfully"
            else:
                error_data = response.json()
                error_msg = error_data.get('detail', 'Invalid or expired OTP')
                print(f"[OTP] ✗ Verification failed: {error_msg}")
                print(f"{'='*60}\n")
                return False, error_msg

        except Exception as e:
            print(f"[OTP ERROR] ✗ {str(e)}")
            print(f"{'='*60}\n")
            return False, "Service unavailable"
