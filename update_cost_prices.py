#!/usr/bin/env python
"""
Script to update cost_price in existing OrderItems from their linked Products
Run this with: python update_cost_prices.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import OrderItem

# Get all OrderItems where cost_price is 0 and product exists
items = OrderItem.objects.filter(cost_price=0).select_related('product')

updated_count = 0
for item in items:
    if item.product and item.product.cost_price:
        item.cost_price = item.product.cost_price
        item.save(update_fields=['cost_price'])
        updated_count += 1
        print(f"Updated {item.product_name}: cost_price = ₹{item.cost_price}")

print(f"\n✓ Total updated: {updated_count} items")
