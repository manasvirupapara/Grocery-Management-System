import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import SubCategory

# Find and remove duplicate subcategories
subcategories = SubCategory.objects.all()
seen = set()
duplicates = []

for subcat in subcategories:
    key = (subcat.category_id, subcat.name)
    if key in seen:
        duplicates.append(subcat)
        print(f"Found duplicate: {subcat.name} in category {subcat.category.name} (ID: {subcat.id})")
    else:
        seen.add(key)

if duplicates:
    print(f"\nRemoving {len(duplicates)} duplicate subcategories...")
    for dup in duplicates:
        dup.delete()
        print(f"✓ Deleted: {dup.name} (ID: {dup.id})")
    print(f"\n✓ Successfully removed {len(duplicates)} duplicates!")
else:
    print("No duplicates found!")
