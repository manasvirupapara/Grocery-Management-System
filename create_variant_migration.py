"""
Script to create migration for Product Variant System
Run this after adding the models to your models.py file
"""

import os
import sys

print("=" * 60)
print("PRODUCT VARIANT SYSTEM - MIGRATION SETUP")
print("=" * 60)
print()

print("Step 1: Copy models from models_variant.py to store/models.py")
print("   - Add Product and ProductVariant models")
print("   - Or replace existing Product model")
print()

print("Step 2: Create migrations")
print("   Run: python manage.py makemigrations")
print()

print("Step 3: Apply migrations")
print("   Run: python manage.py migrate")
print()

print("Step 4: Update admin.py")
print("   - Copy code from admin_variant.py")
print("   - Register Product and ProductVariant admin")
print()

print("Step 5: Update urls.py")
print("   - Include urls from urls_variant.py")
print("   - Add to your main urlpatterns")
print()

print("Step 6: Create sample data (optional)")
print("   Run: python manage.py shell")
print("   Then run the code below:")
print()
print("-" * 60)
print("""
from store.models import Category, Product, ProductVariant

# Create category
category = Category.objects.create(name="Rice & Grains")

# Create product
product = Product.objects.create(
    name="Basmati Rice",
    category=category,
    description="Premium quality basmati rice",
    is_active=True
)

# Create variants
variants_data = [
    {"weight": "500g", "price": 80, "stock": 50},
    {"weight": "1kg", "price": 150, "stock": 100},
    {"weight": "5kg", "price": 700, "stock": 30},
    {"weight": "10kg", "price": 1350, "stock": 20},
]

for data in variants_data:
    ProductVariant.objects.create(
        product=product,
        weight=data["weight"],
        price=data["price"],
        stock=data["stock"],
        low_stock_alert=10,
        is_active=True
    )

print("Sample data created successfully!")
""")
print("-" * 60)
print()

print("Step 7: Test the system")
print("   - Go to admin panel")
print("   - Create a product with variants")
print("   - Visit product detail page")
print("   - Test weight selection and add to cart")
print()

print("=" * 60)
print("SETUP COMPLETE!")
print("=" * 60)
