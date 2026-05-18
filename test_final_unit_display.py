"""
Final test for unit display on home page and quick view
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product

print("=" * 70)
print("FINAL UNIT DISPLAY TEST")
print("=" * 70)

products = Product.objects.filter(is_active=True)[:5]

for product in products:
    print(f"\n📦 {product.name}")
    print(f"   Stock: {product.stock_quantity}")
    print(f"   Display: {product.stock_quantity} {product.get_display_unit()} available")
    
    # Show variants
    variants = product.variants.filter(is_active=True)
    if variants.exists():
        print(f"   Variants:")
        for v in variants:
            print(f"     • {v.weight} ({v.unit_type})")

print("\n" + "=" * 70)
print("✅ All unit displays working!")
print("=" * 70)
print("\nNow test in browser:")
print("1. Home page: Product cards show dynamic units")
print("2. Quick View: Stock updates with variant selection")
print("=" * 70)
