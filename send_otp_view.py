# Add this to your store/views.py file

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
from datetime import datetime, timedelta

# In-memory OTP storage (use Redis or database in production)
otp_storage = {}


@csrf_exempt
def send_otp_api(request):
    """
    API endpoint to send OTP to mobile number
    POST /api/send-otp/
    Body: {"mobile": "9876543210"}
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile = data.get('mobile', '').strip()
            
            # Validate mobile number
            if not mobile or len(mobile) != 10 or not mobile.isdigit():
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid mobile number'
                }, status=400)
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Store OTP with expiry (5 minutes)
            otp_storage[mobile] = {
                'otp': otp,
                'timestamp': datetime.now(),
                'attempts': 0
            }
            
            # Send SMS using your preferred gateway
            # Uncomment and configure one of these:
            
            # Option 1: MSG91
            # from sms_utils import send_otp_msg91
            # result = send_otp_msg91(mobile, otp)
            
            # Option 2: Twilio
            # from sms_utils import send_otp_twilio
            # result = send_otp_twilio(mobile, otp)
            
            # Option 3: Fast2SMS
            # from sms_utils import send_otp_fast2sms
            # result = send_otp_fast2sms(mobile, otp)
            
            # For demo: Just return success (in production, check SMS result)
            print(f"OTP for {mobile}: {otp}")  # Log for testing
            
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to +91 {mobile}',
                'otp': otp  # Remove this in production!
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)



@csrf_exempt
def verify_otp_api(request):
    """
    API endpoint to verify OTP
    POST /api/verify-otp/
    Body: {"mobile": "9876543210", "otp": "123456"}
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mobile = data.get('mobile', '').strip()
            entered_otp = data.get('otp', '').strip()
            
            # Check if OTP exists for this mobile
            if mobile not in otp_storage:
                return JsonResponse({
                    'success': False,
                    'message': 'No OTP found for this mobile number'
                }, status=400)
            
            stored_data = otp_storage[mobile]
            
            # Check if OTP expired (5 minutes)
            if datetime.now() - stored_data['timestamp'] > timedelta(minutes=5):
                del otp_storage[mobile]
                return JsonResponse({
                    'success': False,
                    'message': 'OTP expired. Please request a new one.'
                }, status=400)
            
            # Check attempts (max 3)
            if stored_data['attempts'] >= 3:
                del otp_storage[mobile]
                return JsonResponse({
                    'success': False,
                    'message': 'Too many failed attempts. Please request a new OTP.'
                }, status=400)
            
            # Verify OTP
            if entered_otp == stored_data['otp']:
                # OTP verified successfully
                del otp_storage[mobile]
                return JsonResponse({
                    'success': True,
                    'message': 'OTP verified successfully'
                })
            else:
                # Wrong OTP
                stored_data['attempts'] += 1
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid OTP. {3 - stored_data["attempts"]} attempts remaining.'
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)


# Add these URL patterns to your urls.py:
"""
from django.urls import path
from . import views

urlpatterns = [
    # ... other patterns
    path('api/send-otp/', views.send_otp_api, name='send_otp'),
    path('api/verify-otp/', views.verify_otp_api, name='verify_otp'),
]
"""
