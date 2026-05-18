import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("Testing email configuration...")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print()

try:
    result = send_mail(
        subject='Test Email from Grocery Admin',
        message='This is a test email to verify email configuration is working properly.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],  # Sending to self for testing
        fail_silently=False,
    )
    
    if result == 1:
        print("✓ Email sent successfully!")
        print(f"Check your inbox at: {settings.EMAIL_HOST_USER}")
    else:
        print("✗ Email sending failed!")
        
except Exception as e:
    print(f"✗ Error sending email: {str(e)}")
    print()
    print("Common issues:")
    print("1. Gmail App Password might be incorrect")
    print("2. 2-Step Verification not enabled on Gmail")
    print("3. Less secure app access might be blocked")
    print("4. Internet connection issue")
