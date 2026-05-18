"""
Debug script to check variant ordering
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductVariant

print("=" * 60)
print("DEBUGGING VARIANT ORDERING")
print("=" * 60)

# Get first product
product = Product.objects.filter(is_active=True).first()

print(f"\n📦 Product: {product.name}")
print(f"   Stock Quantity: {product.stock_quantity}")

# Get all variants
variants = product.variants.filter(is_active=True)
print(f"\n   All Variants (unordered):")
for v in variants:
    print(f"   - ID: {v.id}, Weight: {v.weight}, Unit: {v.unit_type}, Price: ₹{v.price}")

# Get first variant by ID
first_by_id = variants.order_by('id').first()
print(f"\n   First by ID: {first_by_id.weight} - {first_by_id.unit_type}")

# Get first variant by price
first_by_price = variants.order_by('price').first()
print(f"   First by price: {first_by_price.weight} - {first_by_price.unit_type}")

# Get first variant (no ordering)
first_no_order = variants.first()
print(f"   First (no order): {first_no_order.weight} - {first_no_order.unit_type}")

print("\n✅ Debug complete!")
