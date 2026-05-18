#!/usr/bin/env python
"""
Script to:
1. Link OrderItems to Products by matching product_name
2. Update cost_price from linked Products
Run this with: python link_products_and_update_costs.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import OrderItem, Product

# Get all OrderItems
items = OrderItem.objects.all()

linked_count = 0
updated_cost_count = 0

for item in items:
    # Try to link product if not linked
    if not item.product and item.product_name:
        try:
            product = Product.objects.get(name__iexact=item.product_name)
            item.product = product
            item.save(update_fields=['product'])
            linked_count += 1
            print(f"✓ Linked: {item.product_name} -> Product ID {product.id}")
        except Product.DoesNotExist:
            print(f"✗ Product not found: {item.product_name}")
        except Product.MultipleObjectsReturned:
            print(f"! Multiple products found for: {item.product_name}")
    
    # Update cost_price if product is linked and cost_price is 0
    if item.product and item.cost_price == 0 and item.product.cost_price:
        item.cost_price = item.product.cost_price
        item.save(update_fields=['cost_price'])
        updated_cost_count += 1
        print(f"  → Updated cost_price: ₹{item.cost_price}")

print(f"\n✓ Total linked: {linked_count} items")
print(f"✓ Total cost_price updated: {updated_cost_count} items")
