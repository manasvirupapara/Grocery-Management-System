import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grocery_admin.settings')
django.setup()

from django.template import Template, Context
from store.models import Product

# Get first product
product = Product.objects.first()

if product:
    # Test template rendering
    template_str = """
    <div class="price-box">
        {% if product.selling_price > product.get_display_price %}
            <span class="old-price">₹{{ product.selling_price|floatformat:2 }}</span>
        {% endif %}
        <span class="price">₹{{ product.get_display_price|floatformat:2 }}</span>
    </div>
    """
    
    template = Template(template_str)
    context = Context({'product': product})
    rendered = template.render(context)
    
    print("Product:", product.name)
    print("Selling Price:", product.selling_price)
    print("Display Price:", product.get_display_price())
    print("Condition (selling > display):", product.selling_price > product.get_display_price())
    print("\nRendered HTML:")
    print(rendered)
else:
    print("No products found")
