"""
Update existing variants with proper unit_type based on their weight
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import ProductVariant

print("=" * 70)
print("UPDATING VARIANT UNIT TYPES")
print("=" * 70)

variants = ProductVariant.objects.all()
updated_count = 0

for variant in variants:
    weight_lower = variant.weight.lower()
    old_unit = variant.unit_type
    
    # Determine unit_type based on weight string
    if 'kg' in weight_lower:
        variant.unit_type = 'kg'
    elif 'g' in weight_lower and 'kg' not in weight_lower:
        variant.unit_type = 'g'
    elif 'l' in weight_lower and 'ml' not in weight_lower:
        variant.unit_type = 'l'
    elif 'ml' in weight_lower:
        variant.unit_type = 'ml'
    elif 'piece' in weight_lower or 'pc' in weight_lower:
        variant.unit_type = 'piece'
    elif 'pack' in weight_lower:
        variant.unit_type = 'pack'
    elif 'box' in weight_lower:
        variant.unit_type = 'box'
    else:
        # Default to kg for weight-based products
        variant.unit_type = 'kg'
    
    if old_unit != variant.unit_type:
        variant.save()
        print(f"✓ {variant.product.name} - {variant.weight}: {old_unit} → {variant.unit_type}")
        updated_count += 1

print("\n" + "=" * 70)
print(f"✅ Updated {updated_count} variants")
print("=" * 70)
