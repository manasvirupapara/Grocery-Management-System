"""
Test the product variant API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductVariant, Batch
from django.db.models import Sum

# Get first product
product = Product.objects.filter(is_active=True).first()

if not product:
    print("❌ No products found!")
    exit()

print("=" * 70)
print(f"📦 TESTING PRODUCT: {product.name} (ID: {product.id})")
print("=" * 70)

# Check variants
variants = ProductVariant.objects.filter(product=product, is_active=True)
print(f"\n✓ Variants Count: {variants.count()}")

if variants.exists():
    for variant in variants:
        print(f"  • {variant.weight} - ₹{variant.price}")
else:
    print("  ⚠️  No variants found!")

# Check batches
batches = Batch.objects.filter(product=product, quantity__gt=0)
print(f"\n✓ Batches Count: {batches.count()}")

if batches.exists():
    total_stock = batches.aggregate(total=Sum('quantity'))['total'] or 0
    print(f"  • Total Stock: {total_stock} units")
    
    for batch in batches:
        print(f"  • Batch {batch.batch_number}: {batch.quantity} units (Exp: {batch.expiry_date})")
else:
    print("  ⚠️  No batches found!")

# Simulate API response
print("\n" + "=" * 70)
print("API RESPONSE SIMULATION:")
print("=" * 70)

variants_data = []
for variant in variants:
    batches = Batch.objects.filter(product=product, quantity__gt=0).order_by('expiry_date')
    total_stock = batches.aggregate(total=Sum('quantity'))['total'] or 0
    earliest_batch = batches.first()
    expiry_date = earliest_batch.expiry_date if earliest_batch else None
    
    variants_data.append({
        'id': variant.id,
        'weight': variant.weight,
        'price': float(variant.price),
        'stock': total_stock,
        'expiry_date': expiry_date.strftime('%d %b, %Y') if expiry_date else None,
    })

print(f"\nProduct: {product.name}")
print(f"Variants: {len(variants_data)}")
for v in variants_data:
    print(f"  • {v['weight']} - ₹{v['price']} (Stock: {v['stock']}, Exp: {v['expiry_date']})")

print("\n" + "=" * 70)
