import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product

# Get first product
product = Product.objects.first()

if product:
    print(f"Product: {product.name}")
    print(f"Selling Price: {product.selling_price}")
    print(f"Display Price: {product.get_display_price()}")
    print(f"Type of Display Price: {type(product.get_display_price())}")
    print(f"Display Price > Selling Price: {product.selling_price > product.get_display_price()}")
    
    # Check variants
    variants = product.variants.filter(is_active=True).order_by('price')
    print(f"\nVariants count: {variants.count()}")
    for v in variants:
        print(f"  - {v.weight}{v.unit_type}: ₹{v.price}")
else:
    print("No products found")
