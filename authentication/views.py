from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserProfile, OTPVerification  # Import both models
from django.contrib.auth.models import User
from .services import OTPService


def home_view(request):
    """Home page"""
    return render(request, 'home.html')


def login_view(request):
    """Login page - Step 1: Username + Password"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"\n[DEBUG] Login attempt for username: {username}")

        # Authenticate with username and password
        user = authenticate(request, username=username, password=password)

        if user is not None:
            print(f"[DEBUG] User authenticated: {user.email}")

            # Password correct - now send OTP
            print(f"[DEBUG] Calling OTP service...")
            otp_code, expires_in = OTPService.generate_otp(user.email)
            print(
                f"[DEBUG] OTP service returned: code={otp_code}, expires={expires_in}")

            if otp_code:
                # Store user ID in session first
                request.session['pending_user_id'] = user.id
                request.session['pending_user_email'] = user.email
                print(f"[DEBUG] Stored in session: user_id={user.id}")

                # Try to send OTP via email
                from appointments.services import EmailService
                print(f"[DEBUG] Calling Email service...")

                try:
                    email_success, email_message = EmailService.send_otp_email(
                        user.email, otp_code)
                    print(
                        f"[DEBUG] Email service returned: success={email_success}, message={email_message}")

                    if email_success:
                        messages.success(
                            request, f'OTP sent to {user.email}. Please check your inbox.')
                    else:
                        messages.warning(
                            request, f'Email delivery failed. Your OTP code is: {otp_code}')

                except Exception as e:
                    print(
                        f"[DEBUG] Email service exception: {type(e).__name__}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    messages.warning(
                        request, f'Email service unavailable. Your OTP code is: {otp_code}')

                print(f"[DEBUG] Redirecting to verify OTP page")
                return redirect('login_verify_otp')
            else:
                print(f"[DEBUG] OTP generation failed!")
                messages.error(
                    request, 'Failed to generate OTP. Please try again later.')
        else:
            print(f"[DEBUG] Authentication failed for username: {username}")
            messages.error(request, 'Invalid username or password')

    return render(request, 'auth/login.html')


def login_verify_otp_view(request):
    """Login Step 2: Verify OTP and complete login"""
    # Check if there's a pending login
    pending_user_id = request.session.get('pending_user_id')
    pending_email = request.session.get('pending_user_email')

    if not pending_user_id:
        messages.error(request, 'No login in progress. Please login first.')
        return redirect('login_view')

    if request.method == 'POST':
        otp_code = request.POST.get('otp')

        # Verify OTP
        success, message = OTPService.verify_otp(pending_email, otp_code)

        if success:
            # OTP verified - now log the user in
            user = User.objects.get(id=pending_user_id)
            login(request, user)

            # Clear session data
            del request.session['pending_user_id']
            del request.session['pending_user_email']

            # Clear OTP records after successful login
            OTPVerification.objects.filter(email=pending_email).delete()

            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, message)

    return render(request, 'auth/login_verify_otp.html', {
        'email': pending_email
    })


def register_view(request):
    """Register page - Simple registration without OTP"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'auth/register.html')

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'auth/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'auth/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'auth/register.html')

        # Create user directly (no OTP)
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create profile
        UserProfile.objects.create(user=user)

        messages.success(
            request, 'Account created successfully! Please login.')
        return redirect('login_view')

    return render(request, 'auth/register.html')


def logout_view(request):
    """Logout and redirect"""
    # Clear OTP records for this user
    if request.user.is_authenticated:
        try:
            OTPVerification.objects.filter(email=request.user.email).delete()
            print(f"[LOGOUT] Cleared OTP records for {request.user.email}")
        except Exception as e:
            print(f"[LOGOUT] Error clearing OTP records: {e}")

    # Clear pending session data
    if 'pending_user_id' in request.session:
        del request.session['pending_user_id']
    if 'pending_user_email' in request.session:
        del request.session['pending_user_email']

    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    """User profile page"""
    return render(request, 'auth/profile.html')
