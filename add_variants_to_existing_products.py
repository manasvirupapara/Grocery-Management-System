"""
Add default variants to existing products that don't have variants
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductVariant

# Get all active products
products = Product.objects.filter(is_active=True)

print("=" * 70)
print("ADDING VARIANTS TO EXISTING PRODUCTS")
print("=" * 70)

added_count = 0
skipped_count = 0

for product in products:
    # Check if product already has variants
    existing_variants = ProductVariant.objects.filter(product=product)
    
    if existing_variants.exists():
        print(f"\n⏭️  Skipping: {product.name} (already has {existing_variants.count()} variants)")
        skipped_count += 1
        continue
    
    print(f"\n📦 Adding variants to: {product.name}")
    
    # Determine default weights based on category
    category_name = product.category.name if product.category else ''
    
    if 'Fruits' in category_name or 'Vegetables' in category_name or 'Vagetables' in category_name:
        # For fruits & vegetables: piece-based weights
        default_weights = [
            ('250g', 0.5),   # 50% of base price
            ('500g', 1.0),   # 100% of base price
            ('1kg', 1.8),    # 180% of base price
        ]
    elif 'Rice' in category_name or 'Atta' in category_name or 'Dal' in category_name:
        # For rice, atta, dal: larger weights
        default_weights = [
            ('500g', 0.5),
            ('1kg', 1.0),
            ('5kg', 4.5),
            ('10kg', 8.5),
        ]
    elif 'Oil' in category_name:
        # For oils
        default_weights = [
            ('500ml', 0.5),
            ('1L', 1.0),
            ('5L', 4.5),
        ]
    else:
        # Default weights for other products
        default_weights = [
            ('250g', 0.5),
            ('500g', 1.0),
            ('1kg', 1.8),
        ]
    
    # Create variants
    base_price = float(product.selling_price)
    variants_created = 0
    
    for weight, multiplier in default_weights:
        variant_price = base_price * multiplier
        
        ProductVariant.objects.create(
            product=product,
            weight=weight,
            price=variant_price,
            stock=0,  # Stock managed by Batch system
            low_stock_alert=10,
            is_active=True
        )
        
        print(f"  ✓ Created: {weight} - ₹{variant_price:.2f}")
        variants_created += 1
    
    added_count += 1

print("\n" + "=" * 70)
print(f"✅ COMPLETED!")
print(f"   Products with variants added: {added_count}")
print(f"   Products skipped: {skipped_count}")
print("=" * 70)
