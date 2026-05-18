"""
Test template rendering for home page
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from store.models import Product
from django.template import Template, Context

print("=" * 60)
print("TESTING TEMPLATE RENDERING")
print("=" * 60)

# Get first product
product = Product.objects.filter(is_active=True).first()

print(f"\n📦 Product: {product.name}")
print(f"   Stock: {product.stock_quantity}")
print(f"   get_display_unit(): '{product.get_display_unit()}'")
print(f"   get_display_price(): ₹{product.get_display_price()}")

# Test template rendering
template_string = """
Stock: {{ product.stock_quantity }}{{ product.get_display_unit }} available
Price: ₹{{ product.get_display_price|floatformat:2 }}
"""

template = Template(template_string)
context = Context({'product': product})
rendered = template.render(context)

print(f"\n📄 Template Output:")
print(rendered)

# Test with explicit call
print(f"\n🔍 Direct method calls:")
print(f"   product.stock_quantity = {product.stock_quantity}")
print(f"   product.get_display_unit() = '{product.get_display_unit()}'")
print(f"   Combined = '{product.stock_quantity}{product.get_display_unit()}'")

print("\n✅ Test complete!")
