import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Category

# Get all active categories
categories = Category.objects.filter(is_active=True).order_by('name')

print("Active Categories:")
print("-" * 50)
for cat in categories:
    print(f"ID: {cat.id:2d} | Name: {cat.name}")

# Check for duplicates by name
from collections import Counter
names = [c.name for c in categories]
duplicates = [name for name, count in Counter(names).items() if count > 1]

if duplicates:
    print("\n⚠️  Duplicate category names found:")
    for dup_name in duplicates:
        dup_cats = Category.objects.filter(name=dup_name, is_active=True)
        print(f"\n'{dup_name}' appears {dup_cats.count()} times:")
        for cat in dup_cats:
            print(f"  - ID: {cat.id}, Icon: {cat.icon}")
else:
    print("\n✓ No duplicate categories found")
