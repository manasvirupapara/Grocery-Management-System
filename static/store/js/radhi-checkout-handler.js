// Checkout Handler - Backend Integration
// This file handles the checkout form submission

document.addEventListener('DOMContentLoaded', () => {
    loadCheckoutCart();
    
    const checkoutForm = document.getElementById('checkoutForm');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', handleCheckoutSubmit);
    }
});

// Load cart items in checkout page
function loadCheckoutCart() {
    const cartItemsContainer = document.getElementById('checkoutCartItems');
    const cartTotalElement = document.getElementById('checkoutTotal');
    
    if (!cartItemsContainer) return;
    
    const cart = JSON.parse(localStorage.getItem('radhi-cart')) || [];
    
    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p class="empty-cart">Your cart is empty!</p>';
        if (cartTotalElement) cartTotalElement.textContent = '₹0';
        return;
    }
    
    let total = 0;
    cartItemsContainer.innerHTML = '';
    
    cart.forEach(item => {
        const itemTotal = item.price * item.qty;
        total += itemTotal;
        
        const itemElement = document.createElement('div');
        itemElement.className = 'checkout-item';
        itemElement.innerHTML = `
            <img src="${item.img}" alt="${item.name}">
            <div class="item-details">
                <h4>${item.name}</h4>
                <p>Qty: ${item.qty} × ₹${item.price}</p>
            </div>
            <div class="item-total">₹${itemTotal}</div>
        `;
        cartItemsContainer.appendChild(itemElement);
    });
    
    if (cartTotalElement) {
        cartTotalElement.textContent = `₹${total}`;
    }
}

// Handle checkout form submission
async function handleCheckoutSubmit(e) {
    e.preventDefault();
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    
    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    try {
        // Get form data
        const formData = new FormData(e.target);
        const cart = JSON.parse(localStorage.getItem('radhi-cart')) || [];
        
        if (cart.length === 0) {
            throw new Error('Your cart is empty!');
        }
        
        // Prepare checkout data
        const checkoutData = {
            customer_name: formData.get('name'),
            customer_email: formData.get('email'),
            customer_phone: formData.get('phone'),
            customer_location: formData.get('address'),
            customer_gender: formData.get('gender') || 'Male',
            payment_method: formData.get('paymentMethod') || 'COD',
            cart_items: cart.map(item => ({
                product_id: item.id,
                quantity: item.qty
            }))
        };
        
        // Submit to backend
        const response = await fetch('http://127.0.0.1:8000/api/checkout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(checkoutData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Checkout failed');
        }
        
        const result = await response.json();
        
        if (result.success) {
            // Clear cart
            localStorage.removeItem('radhi-cart');
            
            // Show success notification
            showNotification('Order placed successfully! 🎉', 'success');
            
            // Redirect to success page
            setTimeout(() => {
                window.location.href = `radhi-order-success.html?order_id=${result.order_id}`;
            }, 1000);
        } else {
            throw new Error(result.message || 'Checkout failed');
        }
        
    } catch (error) {
        console.error('Checkout error:', error);
        showNotification(error.message || 'Checkout failed. Please try again.', 'error');
        
        // Re-enable button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    }
}

// Notification function (if not already defined)
if (typeof showNotification === 'undefined') {
    function showNotification(message, type = 'success') {
        const colors = {
            success: 'linear-gradient(135deg, #10b981, #059669)',
            error: 'linear-gradient(135deg, #ef4444, #dc2626)',
            warning: 'linear-gradient(135deg, #f59e0b, #d97706)',
            info: 'linear-gradient(135deg, #667eea, #764ba2)'
        };
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 18px 25px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
        `;
        
        notification.innerHTML = `
            <i class="fas ${icons[type]}" style="font-size: 1.5rem;"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}
