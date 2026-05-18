# SMS Utility for sending OTP via SMS Gateway
# You can use Twilio, MSG91, or any other SMS gateway

import requests
import random
import string
from datetime import datetime, timedelta

# Configuration - Replace with your actual credentials
SMS_GATEWAY = 'MSG91'  # Options: 'MSG91', 'TWILIO', 'FAST2SMS'

# MSG91 Configuration
MSG91_AUTH_KEY = 'YOUR_MSG91_AUTH_KEY'
MSG91_SENDER_ID = 'YOUR_SENDER_ID'
MSG91_ROUTE = '4'  # 4 for transactional SMS

# Twilio Configuration
TWILIO_ACCOUNT_SID = 'YOUR_TWILIO_ACCOUNT_SID'
TWILIO_AUTH_TOKEN = 'YOUR_TWILIO_AUTH_TOKEN'
TWILIO_PHONE_NUMBER = 'YOUR_TWILIO_PHONE_NUMBER'

# Fast2SMS Configuration
FAST2SMS_API_KEY = 'YOUR_FAST2SMS_API_KEY'


def generate_otp(length=6):
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_msg91(mobile, otp):
    """Send OTP via MSG91"""
    url = "https://api.msg91.com/api/v5/otp"
    
    payload = {
        "template_id": "YOUR_TEMPLATE_ID",
        "mobile": f"91{mobile}",
        "authkey": MSG91_AUTH_KEY,
        "otp": otp
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error sending SMS via MSG91: {e}")
        return None



def send_otp_twilio(mobile, otp):
    """Send OTP via Twilio"""
    from twilio.rest import Client
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=f"Your OTP for The Daily Grocer is: {otp}. Valid for 5 minutes.",
            from_=TWILIO_PHONE_NUMBER,
            to=f"+91{mobile}"
        )
        
        return {"status": "success", "message_sid": message.sid}
    except Exception as e:
        print(f"Error sending SMS via Twilio: {e}")
        return None


def send_otp_fast2sms(mobile, otp):
    """Send OTP via Fast2SMS"""
    url = "https://www.fast2sms.com/dev/bulkV2"
    
    payload = {
        "route": "otp",
        "sender_id": "FSTSMS",
        "message": f"Your OTP is {otp}",
        "variables_values": otp,
        "flash": 0,
        "numbers": mobile
    }
    
    headers = {
        'authorization': FAST2SMS_API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error sending SMS via Fast2SMS: {e}")
        return None


def send_otp(mobile, otp=None):
    """
    Main function to send OTP
    Automatically generates OTP if not provided
    """
    if not otp:
        otp = generate_otp()
    
    # Choose SMS gateway based on configuration
    if SMS_GATEWAY == 'MSG91':
        result = send_otp_msg91(mobile, otp)
    elif SMS_GATEWAY == 'TWILIO':
        result = send_otp_twilio(mobile, otp)
    elif SMS_GATEWAY == 'FAST2SMS':
        result = send_otp_fast2sms(mobile, otp)
    else:
        print(f"Unknown SMS gateway: {SMS_GATEWAY}")
        return None
    
    return {
        'otp': otp,
        'mobile': mobile,
        'result': result,
        'timestamp': datetime.now().isoformat()
    }


# Example usage
if __name__ == "__main__":
    # Test sending OTP
    mobile = "9876543210"  # Replace with test mobile number
    result = send_otp(mobile)
    
    if result:
        print(f"OTP sent successfully!")
        print(f"Mobile: {result['mobile']}")
        print(f"OTP: {result['otp']}")
        print(f"Timestamp: {result['timestamp']}")
    else:
        print("Failed to send OTP")
