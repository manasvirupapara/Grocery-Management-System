"""
Check if products have variants in database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductVariant

# Get all products
products = Product.objects.filter(is_active=True)[:5]

print("=" * 60)
print("CHECKING PRODUCT VARIANTS")
print("=" * 60)

for product in products:
    variants = ProductVariant.objects.filter(product=product, is_active=True)
    print(f"\n📦 Product: {product.name} (ID: {product.id})")
    print(f"   Category: {product.category.name if product.category else 'N/A'}")
    print(f"   Variants Count: {variants.count()}")
    
    if variants.exists():
        for variant in variants:
            print(f"   ✓ {variant.weight} - ₹{variant.price} (Stock: {variant.stock})")
    else:
        print(f"   ⚠️  No variants found!")

print("\n" + "=" * 60)
print(f"Total Products: {products.count()}")
print(f"Total Variants: {ProductVariant.objects.filter(is_active=True).count()}")
print("=" * 60)
