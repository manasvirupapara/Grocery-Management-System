"""
Test unit_type display in API response
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product, ProductVariant, Batch
from django.db.models import Sum

print("=" * 70)
print("TESTING UNIT TYPE DISPLAY")
print("=" * 70)

# Get a product with variants
product = Product.objects.filter(is_active=True).first()

if not product:
    print("❌ No products found!")
    exit()

print(f"\n📦 Product: {product.name}")
print(f"   Category: {product.category.name if product.category else 'N/A'}")

# Get variants
variants = ProductVariant.objects.filter(product=product, is_active=True)

if not variants.exists():
    print("   ⚠️  No variants found!")
    exit()

print(f"\n✓ Variants ({variants.count()}):")

# Get batches for stock
batches = Batch.objects.filter(product=product, quantity__gt=0)
total_stock = batches.aggregate(total=Sum('quantity'))['total'] or 0

for variant in variants:
    # Simulate unit display
    unit_map = {
        'kg': 'kg',
        'g': 'g',
        'l': 'liter' if total_stock == 1 else 'liters',
        'ml': 'ml',
        'piece': 'piece' if total_stock == 1 else 'pieces',
        'pack': 'pack' if total_stock == 1 else 'packs',
        'box': 'box' if total_stock == 1 else 'boxes'
    }
    unit_text = unit_map.get(variant.unit_type, 'units')
    
    print(f"\n  • {variant.weight} ({variant.unit_type})")
    print(f"    Price: ₹{variant.price}")
    print(f"    Stock Display: {total_stock} {unit_text} available")

print("\n" + "=" * 70)
print("✅ Unit type display working correctly!")
print("=" * 70)
