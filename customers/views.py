from difflib import SequenceMatcher
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer
from .forms import CustomerForm

def customer_list(request):
    customer_list = Customer.objects.all().order_by('-id')
    search = request.GET.get('search', '').strip()
    gender_filter = request.GET.get('gender', '').strip()

    if gender_filter and gender_filter in ('Male', 'Female'):
        customer_list = customer_list.filter(gender=gender_filter)

    if search:
        # Match: name/email/phone/location contains search or vice versa, or fuzzy (typos)
        search_lower = search.lower()
        matching_ids = []
        for cust in customer_list:
            name_l = (cust.name or '').lower().strip()
            email_l = (cust.email or '').lower().strip()
            phone_l = (cust.phone or '').lower().strip()
            location_l = (cust.location or '').lower().strip()
            if (search_lower in name_l or name_l in search_lower or
                    search_lower in email_l or email_l in search_lower or
                    search_lower in phone_l or phone_l in search_lower or
                    search_lower in location_l or location_l in search_lower):
                matching_ids.append(cust.id)
            elif (SequenceMatcher(None, search_lower, name_l).ratio() >= 0.8 or
                  SequenceMatcher(None, search_lower, email_l).ratio() >= 0.8 or
                  SequenceMatcher(None, search_lower, phone_l).ratio() >= 0.8 or
                  SequenceMatcher(None, search_lower, location_l).ratio() >= 0.8):
                matching_ids.append(cust.id)
        customer_list = customer_list.filter(id__in=matching_ids)

    paginator = Paginator(customer_list, 8)   # 🔹 per page 8 customers
    page_number = request.GET.get('page')
    customers = paginator.get_page(page_number)

    return render(request, 'customers/customer_list.html', {
        'customers': customers,
        'search': search,
        'gender_filter': gender_filter,
    })

def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()

    return render(request, 'customers/add_customer.html', {
        'form': form
    })

# VIEW CUSTOMER
def view_customer(request, id):
    from django.db.models import Sum, F
    customer = get_object_or_404(Customer, id=id)
    orders = customer.orders.prefetch_related('items').all()
    
    # Calculate accurate totals for each order - use invoice total if exists, else items total
    for order in orders:
        items = order.items.all()
        
        # Check if invoice exists for this order
        try:
            invoice = order.invoice
            # Use invoice total (includes GST, discount, etc.)
            order.calculated_total_amount = invoice.total_amount
        except:
            # No invoice, calculate simple total from OrderItems
            order.calculated_total_amount = items.aggregate(
                total=Sum(F('quantity') * F('price'))
            )['total'] or 0
    
    return render(request, 'customers/view_customer.html', {
        'customer': customer,
        'orders': orders
    })


# EDIT CUSTOMER
def edit_customer(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'customers/edit_customer.html', {
        'form': form,
        'customer': customer
    })


# DELETE CUSTOMER
def delete_customer(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')

    return render(request, 'customers/delete_customer.html', {
        'customer': customer
    })
