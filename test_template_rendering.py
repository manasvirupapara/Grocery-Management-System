"""
Test template rendering for unit display
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product
from django.template import Template, Context

# Get a product
product = Product.objects.first()

print("=" * 70)
print("TEMPLATE RENDERING TEST")
print("=" * 70)

print(f"\nProduct: {product.name}")
print(f"Stock: {product.stock_quantity}")
print(f"get_display_unit(): '{product.get_display_unit()}'")

# Test template rendering
template_string = "{{ product.stock_quantity }}{{ product.get_display_unit }} available"
template = Template(template_string)
context = Context({'product': product})
rendered = template.render(context)

print(f"\nTemplate: {template_string}")
print(f"Rendered: '{rendered}'")

print("\n" + "=" * 70)
print("If rendered output shows unit, then browser cache is the issue!")
print("Solution: Hard refresh browser (Ctrl+Shift+R) or clear cache")
print("=" * 70)
