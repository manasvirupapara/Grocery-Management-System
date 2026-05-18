"""
Test the complete forgot password flow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.core import mail

print("=" * 70)
print("TESTING FORGOT PASSWORD FLOW")
print("=" * 70)
print()

# Check user exists
user = User.objects.filter(email='manasvi1302@gmail.com').first()
if not user:
    print("✗ User not found!")
    exit()

print(f"✓ User found: {user.username}")
print(f"✓ Email: {user.email}")
print()

# Test the forgot password form submission
client = Client()

print("Simulating forgot password form submission...")
print()

# Clear any existing emails
mail.outbox = []

# Submit the form
response = client.post('/forgot-password/', {
    'email': 'manasvi1302@gmail.com'
})

print(f"Response status: {response.status_code}")
print(f"Redirect URL: {response.url if response.status_code == 302 else 'N/A'}")
print()

# Check if email was sent
if len(mail.outbox) > 0:
    print("=" * 70)
    print("✓ EMAIL SENT!")
    print("=" * 70)
    print()
    
    email = mail.outbox[0]
    print(f"Subject: {email.subject}")
    print(f"From: {email.from_email}")
    print(f"To: {email.to}")
    print()
    print("Email body preview:")
    print("-" * 70)
    print(email.body[:500])
    print("-" * 70)
    print()
    
    if email.alternatives:
        print("✓ HTML version included")
    
else:
    print("✗ No email sent!")
    print()
    print("This might be because:")
    print("  1. Form validation failed")
    print("  2. Email backend not configured")
    print("  3. User email not found")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
