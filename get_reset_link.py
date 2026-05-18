"""
Get a fresh password reset link for immediate use
No need to check email - use this link directly!
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

print()
print("=" * 80)
print("PASSWORD RESET LINK GENERATOR")
print("=" * 80)
print()

# Get user
username = input("Enter username (press Enter for 'manasvi'): ").strip() or 'manasvi'

try:
    user = User.objects.get(username=username)
except User.DoesNotExist:
    print(f"✗ User '{username}' not found!")
    exit()

print(f"✓ User found: {user.username}")
print(f"✓ Email: {user.email}")
print()

# Generate token
token = default_token_generator.make_token(user)
uid = urlsafe_base64_encode(force_bytes(user.pk))

# Create reset URL
reset_url = f"http://localhost:8000/reset/{uid}/{token}/"

print("=" * 80)
print("YOUR PASSWORD RESET LINK:")
print("=" * 80)
print()
print(reset_url)
print()
print("=" * 80)
print()

print("HOW TO USE:")
print("-" * 80)
print("1. Make sure Django server is running:")
print("   python manage.py runserver")
print()
print("2. Copy the link above")
print()
print("3. Paste it in your browser")
print()
print("4. Enter your new password")
print()
print("5. Confirm the password")
print()
print("6. Click 'Reset Password'")
print()
print("=" * 80)
print()

print("IMPORTANT NOTES:")
print("-" * 80)
print("• This link expires in 24 hours")
print("• Can only be used once")
print("• After using, you can login with new password")
print("• No need to check email - use this link directly!")
print()
print("=" * 80)
print()
