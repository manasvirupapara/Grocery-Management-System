"""
Run this script while server is running to test password reset
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

print("Testing Password Reset Email Sending...")
print("=" * 60)

# Get user
user = User.objects.filter(email='manasvi1302@gmail.com').first()

if not user:
    print("✗ User not found with email: manasvi1302@gmail.com")
    exit()

print(f"✓ User found: {user.username} ({user.email})")
print()

# Generate token and uid
token = default_token_generator.make_token(user)
uid = urlsafe_base64_encode(force_bytes(user.pk))

print(f"Generated Token: {token}")
print(f"Generated UID: {uid}")
print()

# Create reset link
reset_link = f"http://localhost:8000/reset/{uid}/{token}/"
print(f"Reset Link: {reset_link}")
print()

# Send email
print("Sending email...")
try:
    subject = "Password Reset Request - Grocery Admin"
    message = f"""
Hello {user.username},

You requested a password reset for your Grocery Admin account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Thanks,
Grocery Admin Team
    """
    
    html_message = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 30px; border-radius: 10px;">
        <h2 style="color: #2e7d32;">Password Reset Request</h2>
        <p>Hello {user.username},</p>
        <p>You requested a password reset for your Grocery Admin account.</p>
        <p>Click the button below to reset your password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background: #2e7d32; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p style="color: #666; font-size: 14px;">Or copy this link:</p>
        <p style="background: white; padding: 10px; border-radius: 5px; word-break: break-all; font-size: 12px;">
            {reset_link}
        </p>
        <p style="color: #666;">This link will expire in 24 hours.</p>
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            Thanks,<br><strong>Grocery Admin Team</strong>
        </p>
    </div>
</body>
</html>
    """
    
    result = send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    
    if result == 1:
        print("✓ Email sent successfully!")
        print(f"✓ Check inbox: {user.email}")
        print()
        print("IMPORTANT: Check these locations:")
        print("1. Inbox")
        print("2. Spam/Junk folder")
        print("3. Promotions tab (if Gmail)")
        print("4. Wait 2-3 minutes for delivery")
    else:
        print("✗ Email sending failed (result = 0)")
        
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
