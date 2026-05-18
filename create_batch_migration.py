"""
Script to create and run migrations for Batch model.

Run this script after adding the Batch model to store/models.py

Usage:
    python create_batch_migration.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.core.management import call_command


def create_and_run_migrations():
    """Create and run migrations for Batch model"""
    
    print("=" * 60)
    print("BATCH MANAGEMENT SYSTEM - MIGRATION SETUP")
    print("=" * 60)
    print()
    
    # Step 1: Create migrations
    print("Step 1: Creating migrations...")
    try:
        call_command('makemigrations', 'store')
        print("✅ Migrations created successfully!")
    except Exception as e:
        print(f"❌ Error creating migrations: {e}")
        return False
    
    print()
    
    # Step 2: Run migrations
    print("Step 2: Running migrations...")
    try:
        call_command('migrate', 'store')
        print("✅ Migrations applied successfully!")
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ BATCH MANAGEMENT SYSTEM SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Go to Django Admin: http://localhost:8000/admin/")
    print("2. Navigate to 'Batches' section")
    print("3. Add batches for your products")
    print("4. Stock will be automatically managed using FIFO method")
    print()
    
    return True


if __name__ == "__main__":
    success = create_and_run_migrations()
    sys.exit(0 if success else 1)
