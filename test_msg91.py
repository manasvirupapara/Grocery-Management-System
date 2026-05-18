#!/usr/bin/env python
"""
Test MSG91 API directly to check if SMS is working
"""

import requests
import random

# Your MSG91 Credentials
AUTH_KEY = "496168Ax9t0Id5Isgc699d699aP1"
TEMPLATE_ID = "699d3d8eaf751c807f0796f2"

# Test mobile number (replace with your actual number)
MOBILE = input("Enter your 10-digit mobile number: ").strip()

if len(MOBILE) != 10 or not MOBILE.isdigit():
    print("❌ Invalid mobile number! Must be 10 digits.")
    exit(1)

# Generate test OTP
otp = str(random.randint(100000, 999999))

print(f"\n🔄 Testing MSG91 API...")
print(f"📱 Mobile: +91 {MOBILE}")
print(f"🔢 OTP: {otp}")
print(f"🔑 Auth Key: {AUTH_KEY}")
print(f"📋 Template ID: {TEMPLATE_ID}")
print(f"\n⏳ Sending SMS...\n")

try:
    url = "https://control.msg91.com/api/v5/otp"
    
    payload = {
        "template_id": TEMPLATE_ID,
        "mobile": f"91{MOBILE}",
        "authkey": AUTH_KEY,
        "otp": otp
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📊 Response Status: {response.status_code}")
    print(f"📄 Response Body: {response.text}")
    print(f"\n" + "="*60)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('type') == 'success':
            print("✅ SUCCESS! SMS sent successfully!")
            print(f"📱 Check your mobile +91 {MOBILE} for OTP")
            print(f"🔢 OTP: {otp}")
        else:
            print("❌ FAILED! MSG91 returned error:")
            print(f"   {result}")
    else:
        print("❌ FAILED! HTTP Error:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        
        # Common error messages
        if "Invalid authentication" in response.text:
            print("\n💡 Fix: Check your Auth Key in MSG91 dashboard")
        elif "Template not found" in response.text:
            print("\n💡 Fix: Check your Template ID in MSG91 dashboard")
        elif "Insufficient balance" in response.text:
            print("\n💡 Fix: Add credits to your MSG91 account")
        elif "Template not approved" in response.text:
            print("\n💡 Fix: Wait for template approval or contact MSG91 support")
            
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    print("\n💡 Possible issues:")
    print("   1. No internet connection")
    print("   2. requests package not installed (run: pip install requests)")
    print("   3. MSG91 API is down")

print("\n" + "="*60)
print("\n📝 Next Steps:")
print("   1. If SMS received: Your setup is working! ✅")
print("   2. If error shown: Fix the issue mentioned above")
print("   3. If no SMS: Check MSG91 dashboard for credits/template status")
print("\n🔗 MSG91 Dashboard: https://msg91.com/")
