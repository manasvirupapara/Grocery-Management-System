import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Category

# Define icons for categories
category_icons = {
    'Fruits & Vegetables': '🥬',
    'Fruits and Vegetables': '🥬',
    'Fruits & Vagetables': '🥬',  # Handle typo
    'Fruits and Vagetables': '🥬',  # Handle typo
    'Tea, Coffee & Sugar': '☕',
    'Tea Coffee & Sugar': '☕',
    'Bakery & Bread': '🍞',
    'Bakery and Bread': '🍞',
    'Atta, Rice & Dal': '🌾',
    'Atta Rice & Dal': '🌾',
    'Cooking Oils & Spices': '🌶️',
    'Cooking Oils and Spices': '🌶️',
    'Personal Care': '🧴',
    'Snacks': '🍿',
    'Cold Drinks': '🥤',
    'Beverages': '🥤',
    'Dairy': '🥛',
    'Frozen Foods': '🧊',
}

# Update categories with icons
categories = Category.objects.all()
updated_count = 0

for category in categories:
    # Check if category name matches any in our icon mapping
    icon = None
    for key, value in category_icons.items():
        if key.lower() in category.name.lower() or category.name.lower() in key.lower():
            icon = value
            break
    
    if icon and (not category.icon or category.icon == 'box'):
        category.icon = icon
        category.save()
        updated_count += 1
        print(f"✓ Updated '{category.name}' with icon: {icon}")
    elif category.icon and category.icon != 'box':
        print(f"→ '{category.name}' already has icon: {category.icon}")
    else:
        print(f"✗ No icon found for '{category.name}' - using default 📦")
        if not category.icon or category.icon == 'box':
            category.icon = '📦'
            category.save()
            updated_count += 1

print(f"\n✅ Updated {updated_count} categories with icons!")
