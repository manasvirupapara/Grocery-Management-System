"""
Create migration for adding unit_type field to ProductVariant
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.core.management import call_command

print("=" * 70)
print("CREATING MIGRATION FOR unit_type FIELD")
print("=" * 70)

try:
    # Create migration
    call_command('makemigrations', 'store', '--name', 'add_unit_type_to_variant')
    print("\n✅ Migration created successfully!")
    print("\nNext step: Run 'python manage.py migrate' to apply the migration")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("=" * 70)
