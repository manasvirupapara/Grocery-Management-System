#!/usr/bin/env python
"""
Force update cost_price in OrderItems from their linked Products
(even if cost_price is already set)
Run this AFTER fixing product prices
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import OrderItem

# Get all OrderItems that have a product link
items = OrderItem.objects.filter(product__isnull=False).select_related('product')

updated_count = 0
for item in items:
    if item.product and item.product.cost_price:
        old_cost = item.cost_price
        item.cost_price = item.product.cost_price
        item.save(update_fields=['cost_price'])
        updated_count += 1
        print(f"✓ {item.product_name}: ₹{old_cost} → ₹{item.cost_price}")

print(f"\n✓ Total updated: {updated_count} items")
