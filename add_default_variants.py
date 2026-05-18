"""
Add default variants to existing products
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductVariant
from decimal import Decimal

# Default weight options for different categories
WEIGHT_OPTIONS = {
    'Atta, Rice & Dal': ['500g', '1kg', '2kg', '5kg', '10kg'],
    'Fruits & Vegetables': ['250g', '500g', '1kg'],
    'Bakery & Biscuits': ['100g', '200g', '500g', '1kg'],
    'Dairy': ['200ml', '500ml', '1L'],
    'Beverages': ['250ml', '500ml', '1L', '2L'],
    'Cooking Oil & Spices': ['100g', '250g', '500g', '1kg'],
    'default': ['250g', '500g', '1kg', '2kg']
}

def add_variants_to_product(product):
    """Add default variants to a product"""
    
    # Get weight options based on category
    category_name = product.category.name if product.category else 'default'
    weights = WEIGHT_OPTIONS.get(category_name, WEIGHT_OPTIONS['default'])
    
    # Base price from product
    base_price = product.selling_price
    
    variants_created = 0
    
    for weight in weights:
        # Check if variant already exists
        if ProductVariant.objects.filter(product=product, weight=weight).exists():
            continue
        
        # Calculate price based on weight
        # For example: 500g = base_price, 1kg = base_price * 1.8, etc.
        weight_multiplier = {
            '100g': 0.4,
            '200g': 0.6,
            '250g': 0.7,
            '500g': 1.0,
            '1kg': 1.8,
            '2kg': 3.5,
            '5kg': 8.5,
            '10kg': 16.0,
            '200ml': 0.6,
            '250ml': 0.7,
            '500ml': 1.0,
            '1L': 1.8,
            '2L': 3.5,
        }
        
        multiplier = weight_multiplier.get(weight, 1.0)
        variant_price = base_price * Decimal(str(multiplier))
        
        # Create variant
        ProductVariant.objects.create(
            product=product,
            weight=weight,
            price=variant_price,
            stock=0,  # Stock will come from batches
            low_stock_alert=10,
            is_active=True
        )
        variants_created += 1
    
    return variants_created

# Main execution
print("=" * 60)
print("ADDING DEFAULT VARIANTS TO PRODUCTS")
print("=" * 60)

products = Product.objects.filter(is_active=True)
total_variants = 0

for product in products:
    count = add_variants_to_product(product)
    if count > 0:
        print(f"✓ {product.name}: Added {count} variants")
        total_variants += count
    else:
        print(f"- {product.name}: Already has variants")

print("\n" + "=" * 60)
print(f"Total variants created: {total_variants}")
print("=" * 60)
print("\n✅ Done! Now refresh your page and check Quick View.")
