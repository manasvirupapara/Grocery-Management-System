from django import forms
from .models import Category, SubCategory, Offer, Tax, Invoice, Product

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'is_active']


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Organic Rice'}),
        }


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['name', 'description', 'discount_type', 'discount_value', 'products', 'categories', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Summer Sale'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Offer description...'}),
            'discount_value': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'products': forms.SelectMultiple(attrs={'size': '5'}),
            'categories': forms.SelectMultiple(attrs={'size': '5'}),
        }


class TaxForm(forms.ModelForm):
    is_active = forms.TypedChoiceField(
        choices=((True, "Active"), (False, "Inactive")),
        coerce=lambda v: v in (True, "True", "true", "1", 1),
        widget=forms.Select(),
        initial=False,
    )

    class Meta:
        model = Tax
        fields = ['tax_name', 'tax_percentage', 'is_active']
        widgets = {
            'tax_name': forms.TextInput(attrs={'placeholder': 'e.g. GST'}),
            'tax_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class InvoiceUpdateForm(forms.ModelForm):
    """Admin-side updates: discount, payment status, notes."""
    class Meta:
        model = Invoice
        fields = ['discount', 'payment_status', 'notes']
        widgets = {
            'discount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'subcategory', 'sku', 'image', 'stock_quantity', 'low_stock_threshold', 
                  'expiry_date', 'cost_price', 'selling_price', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Basmati Rice'}),
            'sku': forms.TextInput(attrs={'placeholder': 'e.g. RICE-001'}),
            'stock_quantity': forms.NumberInput(attrs={'min': '0'}),
            'low_stock_threshold': forms.NumberInput(attrs={'min': '0'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'cost_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'selling_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields optional
        self.fields['stock_quantity'].required = False
        self.fields['low_stock_threshold'].required = False
        self.fields['cost_price'].required = False
        self.fields['sku'].required = False
        self.fields['expiry_date'].required = False
        self.fields['description'].required = False
        self.fields['subcategory'].required = False
        self.fields['category'].required = False
        # Set defaults
        if not self.instance.pk:
            self.fields['stock_quantity'].initial = 0
            self.fields['low_stock_threshold'].initial = 10
