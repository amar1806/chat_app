import json
from django.shortcuts import render, redirect  # <--- Added this line
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import login
from django.contrib.auth import logout
from django.db.models import Q
from .models import CustomUser
from .utils import generate_otp, verify_otp_logic

# This loads the ONE single HTML page
@ensure_csrf_cookie
def auth_page(request):
    return render(request, 'accounts/auth.html')

# --- API ENDPOINTS (Called by JavaScript) ---

def api_send_otp(request):
    """Step 1: Receive Mobile/Email -> Send OTP"""
    if request.method == "POST":
        data = json.loads(request.body)
        identifier = data.get('mobile') # Or email
        action = data.get('action') # 'login' or 'signup'

        # Check availability for signup
        if action == 'signup' and CustomUser.objects.filter(mobile=identifier).exists():
            return JsonResponse({'success': False, 'message': 'Mobile already registered. Please Login.'})
        
        # Check existence for login
        if action == 'login' and not CustomUser.objects.filter(mobile=identifier).exists():
            return JsonResponse({'success': False, 'message': 'User not found. Please Signup.'})

        # Generate OTP
        generate_otp(identifier)
        
        # Save temp data in session
        request.session['auth_mobile'] = identifier
        request.session['auth_data'] = data # Store name/email for signup later
        
        return JsonResponse({'success': True, 'message': 'OTP Sent!'})
    return JsonResponse({'success': False})

def api_verify_otp(request):
    """Step 2: Verify OTP"""
    if request.method == "POST":
        data = json.loads(request.body)
        otp = data.get('otp')
        mobile = request.session.get('auth_mobile')

        if verify_otp_logic(mobile, otp):
            request.session['is_verified'] = True
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid OTP'})

def api_complete_profile(request):
    """Step 3: Create User (Signup only)"""
    if request.method == "POST":
        if not request.session.get('is_verified'):
            return JsonResponse({'success': False, 'message': 'Not Verified'})

        data = json.loads(request.body)
        saved_data = request.session.get('auth_data', {})
        
        # Create User
        try:
            user = CustomUser.objects.create_user(
                username=data['username'],
                dob=data['dob'],
                mobile=saved_data['mobile'],
                email=saved_data.get('email', ''),
                first_name=saved_data.get('first_name', ''),
                last_name=saved_data.get('last_name', ''),
                is_mobile_verified=True
            )
            login(request, user)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

def api_login_success(request):
    """Final Step for Login: Log the user in after OTP"""
    if request.method == "POST":
        mobile = request.session.get('auth_mobile')
        if request.session.get('is_verified'):
            user = CustomUser.objects.get(mobile=mobile)
            login(request, user)
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# logout view
def logout_view(request):
    logout(request)
    return redirect('auth_home')