"""
Manually update stock to test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import ProductVariant

print("=" * 60)
print("MANUAL STOCK UPDATE TEST")
print("=" * 60)

# Get all variants
variants = ProductVariant.objects.all()[:5]

print("\nUpdating stock for first 5 variants:")
for i, variant in enumerate(variants, 1):
    old_stock = variant.stock
    new_stock = 10 + (i * 5)  # 15, 20, 25, 30, 35
    
    variant.stock = new_stock
    variant.save()
    
    # Verify
    variant.refresh_from_db()
    print(f"{i}. {variant.product.name} - {variant.weight}")
    print(f"   Old Stock: {old_stock} → New Stock: {variant.stock}")
    
    if variant.stock == new_stock:
        print(f"   ✅ Success!")
    else:
        print(f"   ❌ Failed! Expected {new_stock}, got {variant.stock}")

print("\n" + "=" * 60)
print("Now check admin panel - stock should be updated!")
print("=" * 60)
