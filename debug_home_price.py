import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product

# Get first 3 products
products = Product.objects.all()[:3]

for product in products:
    print(f"\n{'='*50}")
    print(f"Product: {product.name}")
    print(f"Selling Price: ₹{product.selling_price}")
    print(f"Display Price: ₹{product.get_display_price()}")
    print(f"Condition (selling > display): {product.selling_price > product.get_display_price()}")
    
    # Check variants
    variants = product.variants.filter(is_active=True).order_by('price')
    print(f"\nVariants ({variants.count()}):")
    for v in variants:
        print(f"  - {v.weight}{v.unit_type}: ₹{v.price}")
    
    # Simulate template rendering
    display_price = product.get_display_price()
    selling_price = product.selling_price
    
    print(f"\nTemplate would render:")
    print(f'  <strong style="font-size: 24px; color: rgb(40, 167, 69);">₹{display_price:.2f}</strong>')
    if selling_price > display_price:
        print(f'  <span style="font-size: 16px; color: rgb(153, 153, 153); text-decoration: line-through; margin-left: 8px;">₹{selling_price:.2f}</span>')
