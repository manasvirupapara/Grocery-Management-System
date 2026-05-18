import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.conf import settings

print("=" * 60)
print("FORGOT PASSWORD FLOW TEST")
print("=" * 60)
print()

# Check email settings
print("1. Email Configuration:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print()

# Check if users exist
print("2. Checking Users:")
users = User.objects.all()
if users.exists():
    print(f"   Total users: {users.count()}")
    for user in users:
        print(f"   - Username: {user.username}, Email: {user.email}")
else:
    print("   ✗ No users found in database!")
    print("   Create a user first using: python manage.py createsuperuser")
print()

# Test password reset for first user with email
print("3. Testing Password Reset Email:")
user_with_email = User.objects.exclude(email='').first()

if user_with_email:
    print(f"   Testing for: {user_with_email.username} ({user_with_email.email})")
    
    form = PasswordResetForm({'email': user_with_email.email})
    
    if form.is_valid():
        try:
            # This will send the email
            form.save(
                request=None,
                use_https=False,
                from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name='registration/password_reset_email.html',
            )
            print("   ✓ Password reset email sent successfully!")
            print(f"   Check inbox: {user_with_email.email}")
        except Exception as e:
            print(f"   ✗ Error sending email: {str(e)}")
    else:
        print(f"   ✗ Form validation failed: {form.errors}")
else:
    print("   ✗ No user with email found!")
    print("   Add email to user: python manage.py shell")
    print("   >>> from django.contrib.auth.models import User")
    print("   >>> user = User.objects.first()")
    print("   >>> user.email = 'your@email.com'")
    print("   >>> user.save()")

print()
print("=" * 60)
print("TROUBLESHOOTING TIPS:")
print("=" * 60)
print("1. Make sure user has email address set")
print("2. Check spam/junk folder")
print("3. Verify Gmail App Password is correct")
print("4. Ensure 2-Step Verification is enabled on Gmail")
print("5. Check if 'Less secure app access' is enabled (if needed)")
print("6. Run server and test via browser: http://localhost:8000/forgot-password/")
print("=" * 60)
