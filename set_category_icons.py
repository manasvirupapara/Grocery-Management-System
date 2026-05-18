import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Category

# Icon mapping based on category names
icon_mapping = {
    'Vegetables': '🥬',
    'Fruits': '🍎',
    'Bakery & Bread': '🍞',
    'Bakery': '🍞',
    'Bread': '🍞',
    'Grains': '🌾',
    'Dairy': '🥛',
    'Cooking Oils & Spices': '🌶️',
    'Oils': '🌶️',
    'Spices': '🌶️',
    'Frozen Foods': '🧊',
    'Frozen': '🧊',
    'Personal Care': '🧴',
    'Household & Cleaning': '🧹',
    'Household': '🧹',
    'Cleaning': '🧹',
    'Meat, Fish & Eggs': '🍖',
    'Meat': '🍖',
    'Fish': '🐟',
    'Eggs': '🥚',
    'Snacks': '🍿',
    'Drinks': '🧃',
    'Beverages': '🧃',
    'Breakfast': '🥣',
    'Instant': '🥣',
    'Sweet': '🍫',
    'Candy': '🍫',
    'Biscuits': '🍪',
    'Cookies': '🍪',
    'Atta': '🌾',
    'Rice': '🌾',
    'Dal': '🌾',
    'Masala': '🌶️',
    'Ghee': '🧈'
}

# Update all categories
categories = Category.objects.all()
updated_count = 0

for category in categories:
    if category.name in icon_mapping:
        category.icon = icon_mapping[category.name]
        category.save()
        print(f"✅ Updated {category.name} with icon {category.icon}")
        updated_count += 1
    else:
        # Set default icon for categories not in mapping
        category.icon = '📦'
        category.save()
        print(f"⚠️  Set default icon for {category.name}")
        updated_count += 1

print(f"\n🎉 Successfully updated {updated_count} categories!")
