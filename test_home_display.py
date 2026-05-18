"""
Test script to verify home page display issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductVariant

print("=" * 60)
print("TESTING HOME PAGE DISPLAY")
print("=" * 60)

# Get first 5 products
products = Product.objects.filter(is_active=True)[:5]

for product in products:
    print(f"\n📦 Product: {product.name}")
    print(f"   Stock Quantity: {product.stock_quantity}")
    
    # Test get_display_unit
    unit = product.get_display_unit()
    print(f"   get_display_unit(): '{unit}'")
    
    # Test get_display_price
    price = product.get_display_price()
    print(f"   get_display_price(): ₹{price}")
    
    # Check variants
    variants = product.variants.filter(is_active=True)
    print(f"   Variants count: {variants.count()}")
    
    if variants.exists():
        first_variant = variants.first()
        print(f"   First variant: {first_variant.weight} - ₹{first_variant.price} - unit_type: {first_variant.unit_type}")
    
    # Test template output
    template_output = f"{product.stock_quantity}{unit} available"
    print(f"   Template output: '{template_output}'")
    
    print("-" * 60)

print("\n✅ Test complete!")
