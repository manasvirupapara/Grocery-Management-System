import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Category

# Find and update Fruits & Vagetables category
try:
    category = Category.objects.get(name__icontains='Fruits')
    category.icon = '🥬'
    category.save()
    print(f"✅ Updated '{category.name}' with icon: 🥬")
except Category.DoesNotExist:
    print("❌ Fruits category not found")
except Exception as e:
    print(f"❌ Error: {e}")
