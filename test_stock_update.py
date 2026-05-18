"""
Test stock update functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import ProductVariant

print("=" * 60)
print("TESTING STOCK UPDATE")
print("=" * 60)

# Get first variant
variant = ProductVariant.objects.first()
print(f"\nBefore Update:")
print(f"  Variant: {variant.weight}")
print(f"  Stock: {variant.stock}")

# Update stock
variant.stock = 15
variant.save()

# Refresh and check
variant.refresh_from_db()
print(f"\nAfter Update:")
print(f"  Variant: {variant.weight}")
print(f"  Stock: {variant.stock}")

if variant.stock == 15:
    print("\n✅ Stock update working correctly!")
else:
    print(f"\n❌ Stock update failed! Expected 15, got {variant.stock}")

print("=" * 60)
