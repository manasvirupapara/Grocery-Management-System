"""
Direct test to send password reset email to your inbox
Run this to verify email is being sent
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string

print("=" * 70)
print("SENDING PASSWORD RESET EMAIL")
print("=" * 70)
print()

# Get user
user = User.objects.filter(email='manasvi1302@gmail.com').first()

if not user:
    print("✗ User not found!")
    exit()

print(f"✓ User: {user.username}")
print(f"✓ Email: {user.email}")
print()

# Generate token
token = default_token_generator.make_token(user)
uid = urlsafe_base64_encode(force_bytes(user.pk))

print(f"Token: {token}")
print(f"UID: {uid}")
print()

# Create reset URL
reset_url = f"http://localhost:8000/reset/{uid}/{token}/"
print(f"Reset URL: {reset_url}")
print()

# Email content
subject = "Password Reset - Grocery Admin"

# Plain text version
text_content = f"""
Hello {user.username},

You requested a password reset for your Grocery Admin account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Thanks,
Grocery Admin Team
"""

# HTML version
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%); padding: 40px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 32px;">🛒 Grocery Admin</h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="color: #2e7d32; margin: 0 0 20px 0; font-size: 24px;">Password Reset Request</h2>
                            
                            <p style="color: #333; font-size: 16px; line-height: 1.6; margin: 0 0 15px 0;">
                                Hello <strong>{user.username}</strong>,
                            </p>
                            
                            <p style="color: #333; font-size: 16px; line-height: 1.6; margin: 0 0 15px 0;">
                                You requested a password reset for your Grocery Admin account.
                            </p>
                            
                            <p style="color: #333; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                Click the button below to reset your password:
                            </p>
                            
                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{reset_url}" style="background-color: #2e7d32; color: #ffffff; padding: 15px 40px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; font-size: 16px;">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #666; font-size: 14px; line-height: 1.6; margin: 20px 0;">
                                Or copy and paste this link in your browser:
                            </p>
                            
                            <p style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; word-break: break-all; font-size: 12px; color: #333; border: 1px solid #e0e0e0;">
                                {reset_url}
                            </p>
                            
                            <!-- Warning Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 5px;">
                                        <p style="margin: 0; color: #856404; font-size: 14px;">
                                            <strong>⚠️ Important:</strong> This link will expire in 24 hours.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #666; font-size: 14px; line-height: 1.6; margin: 0;">
                                If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="color: #999; font-size: 12px; margin: 0;">
                                Thanks,<br>
                                <strong style="color: #2e7d32;">Grocery Admin Team</strong>
                            </p>
                            <p style="color: #999; font-size: 11px; margin: 10px 0 0 0;">
                                This is an automated email. Please do not reply.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

# Send email
print("Sending email...")
print()

try:
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    result = msg.send()
    
    if result == 1:
        print("=" * 70)
        print("✓ EMAIL SENT SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"📧 Sent to: {user.email}")
        print()
        print("IMPORTANT: Check these locations:")
        print("  1. 📥 Inbox")
        print("  2. 🗑️  Spam/Junk folder (MOST LIKELY HERE!)")
        print("  3. 📊 Promotions tab (if Gmail)")
        print("  4. 🔍 Search for 'Grocery Admin' in email")
        print("  5. ⏰ Wait 2-5 minutes for delivery")
        print()
        print("If still not received:")
        print("  - Check email filters/rules")
        print("  - Verify email address is correct")
        print("  - Try different email address")
        print()
        print("=" * 70)
    else:
        print("✗ Email sending failed (result = 0)")
        
except Exception as e:
    print(f"✗ Error: {str(e)}")
    print()
    import traceback
    traceback.print_exc()

print()
print("You can now use this link to reset password:")
print(reset_url)
print()
