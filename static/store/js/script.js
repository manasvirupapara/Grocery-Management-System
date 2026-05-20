// Home page Add to Cart - data attributes se safe call
function homeAddToCart(btn) {
    const id = btn.getAttribute('data-id');
    const name = btn.getAttribute('data-name');
    const price = parseFloat(btn.getAttribute('data-price')) || 0;
    const original = parseFloat(btn.getAttribute('data-original')) || price;
    const discount = parseFloat(btn.getAttribute('data-discount')) || 0;
    addToCartFull(id, name, price, original, discount, '');
}

// Full Add to Cart with original price, discount, weight
function addToCartFull(productId, productName, productPrice, originalPrice, discountPct, weight) {
    try {
        if (!isUserLoggedIn()) {
            showNotification('⚠️ Please login to add items to cart!');
            setTimeout(() => { window.location.href = '/auth/'; }, 1500);
            return;
        }
        productPrice = parseFloat(productPrice) || 0;
        originalPrice = parseFloat(originalPrice) || productPrice;
        discountPct = parseFloat(discountPct) || 0;
        weight = weight || '';
        
        let cart = JSON.parse(localStorage.getItem('radhi-cart') || '[]');
        const existingItem = cart.find(item => 
            String(item.id) === String(productId) && (item.weight || '') === weight
        );
        if (existingItem) {
            if (existingItem.qty >= 8) { showNotification('⚠️ Maximum 8 items allowed!'); return; }
            existingItem.qty++;
        } else {
            const imgEl = document.querySelector(`[data-id="${productId}"] img`);
            cart.push({ id: productId, name: productName, price: productPrice, originalPrice, discountPct, qty: 1, weight, img: imgEl ? imgEl.src : '' });
        }
        localStorage.setItem('radhi-cart', JSON.stringify(cart));
        const cc = document.querySelector('#cartCount');
        if (cc) cc.textContent = cart.length;
        showNotification('🛒 Product added to cart!');
        updateDatabaseStock(productId, -1);
    } catch(e) { console.error('addToCartFull error:', e); }
}

// Add to Cart Function - Simple version (working)
function addToCart(productId, productName, productPrice) {
    // Check if user is logged in
    if (!isUserLoggedIn()) {
        showNotification('⚠️ Please login to add items to cart!');
        setTimeout(() => {
            window.location.href = '/auth/';
        }, 1500);
        return;
    }
    
    // Ensure price is a valid number
    productPrice = parseFloat(productPrice) || 0;
    
    let cart = JSON.parse(localStorage.getItem('radhi-cart')) || [];
    
    // Find existing item with same ID AND same price (same weight)
    const existingItem = cart.find(item => item.id === productId && parseFloat(item.price) === productPrice);
    
    if (existingItem) {
        if (existingItem.qty >= 8) {
            showNotification('⚠️ Maximum 8 items allowed per product!');
            return;
        }
        existingItem.qty++;
    } else {
        const imgElement = document.querySelector(`[data-id="${productId}"] img`);
        cart.push({
            id: productId,
            name: productName,
            price: productPrice,
            qty: 1,
            weight: '',
            img: imgElement ? imgElement.src : ''
        });
    }
    
    // Save to localStorage
    localStorage.setItem('radhi-cart', JSON.stringify(cart));
    
    // Update cart count immediately
    const cartCount = document.querySelector('#cartCount');
    if (cartCount) {
        cartCount.textContent = cart.length;
    }
    
    showNotification('🛒 Product added to cart!');
    
    // Button animation
    try {
        const button = event.target.closest('button');
        if (button) {
            button.classList.add('added');
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Added';
            setTimeout(() => {
                button.classList.remove('added');
                button.innerHTML = originalHTML;
            }, 1500);
        }
    } catch (e) {
        console.log('Button animation skipped');
    }
    
    // TODO: Call database API in background
    updateDatabaseStock(productId, -1);
}

// Add to Cart with Weight - For weight-based products
function addToCartWithWeight(productId, productName, productPrice, weight, quantity) {
    // Check if user is logged in
    if (!isUserLoggedIn()) {
        showNotification('⚠️ Please login to add items to cart!');
        setTimeout(() => {
            window.location.href = '/auth/';
        }, 1500);
        return;
    }
    
    // Ensure price is a valid number
    productPrice = parseFloat(productPrice) || 0;
    quantity = parseInt(quantity) || 1;
    
    console.log('Adding to cart:', { productId, productName, productPrice, weight, quantity });
    
    let cart = JSON.parse(localStorage.getItem('radhi-cart')) || [];
    
    // Find existing item with same ID AND weight (not price, as price is derived from weight)
    const existingItem = cart.find(item => 
        item.id === productId && 
        item.weight === weight
    );
    
    console.log('Existing item found:', existingItem);
    
    if (existingItem) {
        const newQty = existingItem.qty + quantity;
        if (newQty > 8) {
            showNotification(`⚠️ Maximum 8 items allowed! (Already have ${existingItem.qty})`);
            return;
        }
        existingItem.qty = newQty;
        console.log('Updated quantity:', existingItem.qty);
    } else {
        const imgElement = document.querySelector(`[data-id="${productId}"] img`);
        const newItem = {
            id: productId,
            name: productName,
            price: productPrice,
            weight: weight,
            qty: quantity,
            img: imgElement ? imgElement.src : ''
        };
        cart.push(newItem);
        console.log('Added new item:', newItem);
    }
    
    // Save to localStorage
    localStorage.setItem('radhi-cart', JSON.stringify(cart));
    console.log('Cart saved:', cart);
    
    // Update cart count immediately
    const cartCount = document.querySelector('#cartCount');
    if (cartCount) {
        cartCount.textContent = cart.length;
    }
    
    showNotification('🛒 Product added to cart!');
    
    // TODO: Call database API in background
    updateDatabaseStock(productId, -quantity);
}

// Update database stock in background (non-blocking)
async function updateDatabaseStock(productId, quantityChange) {
    try {
        console.log('Updating database stock:', { productId, quantityChange });
        
        const endpoint = quantityChange < 0 ? '/api/cart/add/' : '/api/cart/remove/';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                quantity: Math.abs(quantityChange)
            })
        });
        
        const data = await response.json();
        console.log('Database response:', data);
        
        if (data.success) {
            // Update stock display on page with category info
            updateStockDisplay(
                productId, 
                data.remaining_stock, 
                data.is_low_stock, 
                data.is_out_of_stock,
                data.category_name || ''
            );
            console.log('Stock updated successfully. New stock:', data.remaining_stock);
        } else {
            console.log('Stock update failed:', data.message);
            showNotification('⚠️ ' + data.message);
        }
    } catch (error) {
        console.error('Database update error:', error);
        showNotification('⚠️ Failed to update stock');
    }
}

// Update stock display on product card
function updateStockDisplay(productId, newStock, isLowStock, isOutOfStock, categoryName) {
    const productCard = document.querySelector(`[data-product-id="${productId}"]`);
    if (!productCard) return;
    
    // Get unit type from data attribute
    const stockDiv = productCard.querySelector('.product-stock');
    let unitType = 'kg'; // default
    if (stockDiv) {
        unitType = stockDiv.getAttribute('data-unit-type') || 'kg';
    }
    
    // Map unit_type to display text
    function getUnitText(unitType, quantity) {
        const unitMap = {
            'kg': 'kg',
            'g': 'g',
            'l': quantity === 1 ? ' liter' : ' liters',
            'ml': 'ml',
            'piece': quantity === 1 ? ' piece' : ' pieces',
            'pack': quantity === 1 ? ' pack' : ' packs',
            'box': quantity === 1 ? ' box' : ' boxes'
        };
        return unitMap[unitType] || ' units';
    }
    
    const unitText = getUnitText(unitType, newStock);
    
    // Update stock info text in product-stock div
    if (stockDiv) {
        const stockSpan = stockDiv.querySelector('.in-stock, .out-of-stock-text');
        if (stockSpan) {
            if (newStock > 0) {
                stockSpan.className = 'in-stock';
                stockSpan.textContent = `${newStock}${unitText} available`;
            } else {
                stockSpan.className = 'out-of-stock-text';
                stockSpan.textContent = 'Out of Stock';
            }
        }
    }
    
    // Update or add badge
    let badgeContainer = productCard.querySelector('.product-badges');
    if (!badgeContainer) {
        badgeContainer = document.createElement('div');
        badgeContainer.className = 'product-badges';
        const productImage = productCard.querySelector('.product-image');
        if (productImage) {
            productImage.insertBefore(badgeContainer, productImage.firstChild);
        }
    }
    
    let badge = badgeContainer.querySelector('.badge');
    
    if (isOutOfStock) {
        if (badge) {
            badge.className = 'badge out-of-stock';
            badge.textContent = 'OUT OF STOCK';
        } else {
            badge = document.createElement('span');
            badge.className = 'badge out-of-stock';
            badge.textContent = 'OUT OF STOCK';
            badgeContainer.appendChild(badge);
        }
        
        // Disable add to cart button
        const addBtn = productCard.querySelector('.add-cart-btn');
        if (addBtn) {
            addBtn.disabled = true;
            addBtn.innerHTML = '<i class="fas fa-ban"></i> Out of Stock';
        }
    } else if (isLowStock) {
        if (badge) {
            badge.className = 'badge low-stock';
            badge.textContent = 'LOW STOCK';
        } else {
            badge = document.createElement('span');
            badge.className = 'badge low-stock';
            badge.textContent = 'LOW STOCK';
            badgeContainer.appendChild(badge);
        }
    } else {
        // Remove out of stock or low stock badge if stock is normal
        if (badge && (badge.textContent === 'LOW STOCK' || badge.textContent === 'OUT OF STOCK')) {
            badge.remove();
        }
    }
}

// Toggle Wishlist Function
function toggleWishlist(productId, productName, productPrice) {
    // Check if user is logged in
    if (!isUserLoggedIn()) {
        showNotification('⚠️ Please login to add items to wishlist!');
        setTimeout(() => {
            window.location.href = '/auth/';
        }, 1500);
        return;
    }
    
    let wishlist = JSON.parse(localStorage.getItem('radhi-wishlist')) || [];
    
    // Convert productId to string for consistent comparison
    const idToCheck = String(productId);
    const existingIndex = wishlist.findIndex(item => String(item.id) === idToCheck);
    const button = event.target.closest('button');
    
    if (existingIndex > -1) {
        // Remove from wishlist
        wishlist.splice(existingIndex, 1);
        button.classList.remove('active');
        showNotification('❤️ Removed from wishlist!');
        console.log('Removed from wishlist. ID:', productId, 'Remaining items:', wishlist.length);
    } else {
        // Add to wishlist
        const productCard = button.closest('.product-card');
        const productImage = productCard.querySelector('.product-image img').src;
        
        wishlist.push({ 
            id: productId, 
            name: productName, 
            price: productPrice, 
            image: productImage 
        });
        
        button.classList.add('active');
        showNotification('❤️ Added to wishlist!');
        console.log('Added to wishlist. ID:', productId, 'Total items:', wishlist.length);
    }
    
    // Save and update count
    localStorage.setItem('radhi-wishlist', JSON.stringify(wishlist));
    
    // Update wishlist count in navbar immediately
    const wishlistCount = document.querySelector('#wishlistCount');
    if (wishlistCount) {
        wishlistCount.textContent = wishlist.length;
    }
    
    console.log('Current wishlist:', JSON.stringify(wishlist));
}

// Quick View Function
function quickView(productId) {
    showNotification('Quick view feature coming soon!');
    // You can implement modal popup here
}

// Cart and Wishlist Data
let cart = [];
let wishlist = [];

// Check if user is logged in
function isUserLoggedIn() {
    try {
        const user = JSON.parse(sessionStorage.getItem('radhi-user') || '{}');
        return user.loggedIn === true && !user.isGuest;
    } catch {
        return false;
    }
}

// Load cart and wishlist only if user is logged in
if (isUserLoggedIn()) {
    cart = JSON.parse(localStorage.getItem('radhi-cart')) || [];
    wishlist = JSON.parse(localStorage.getItem('radhi-wishlist')) || [];
} else {
    // Not logged in - clear any existing data and show 0
    cart = [];
    wishlist = [];
}

// Update Cart Display
function updateCart() {
    // Re-check login status
    if (!isUserLoggedIn()) {
        cart = [];
    }
    
    const cartCount = document.querySelector('#cartCount');
    if (cartCount) {
        // Show total number of unique items (not quantity)
        cartCount.textContent = cart.length;
    }
    
    // Save to localStorage only if logged in
    if (isUserLoggedIn()) {
        localStorage.setItem('radhi-cart', JSON.stringify(cart));
    }
    
    const cartBody = document.getElementById('cartBody');
    if (!cartBody) return;
    
    if (cart.length === 0) {
        cartBody.innerHTML = '<p class="empty-message">Your cart is empty</p>';
        const cartTotal = document.getElementById('cartTotal');
        if (cartTotal) cartTotal.textContent = '₹0';
        return;
    }
    
    cartBody.innerHTML = cart.map(item => `
        <div class="cart-item">
            <img src="${item.img || item.image}" alt="${item.name}">
            <div class="item-details">
                <h4>${item.name}</h4>
                <p class="item-price">₹${item.price}</p>
                <div class="item-quantity">
                    <button class="qty-btn" onclick="updateQuantity('${item.id}', -1)">-</button>
                    <span>${item.qty}</span>
                    <button class="qty-btn" onclick="updateQuantity('${item.id}', 1)">+</button>
                </div>
            </div>
            <button class="remove-btn" onclick="removeFromCart('${item.id}')">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
    
    const total = cart.reduce((sum, item) => sum + (item.price * (item.qty || 0)), 0);
    const cartTotal = document.getElementById('cartTotal');
    if (cartTotal) cartTotal.textContent = `₹${total}`;
}

// Update Wishlist Display
function updateWishlist() {
    // Re-check login status
    if (!isUserLoggedIn()) {
        wishlist = [];
    }
    
    // Remove duplicates based on ID
    const uniqueWishlist = [];
    const seenIds = new Set();
    
    wishlist.forEach(item => {
        if (!seenIds.has(item.id)) {
            seenIds.add(item.id);
            uniqueWishlist.push(item);
        }
    });
    
    wishlist = uniqueWishlist;
    
    const wishlistCount = document.querySelector('#wishlistCount');
    if (wishlistCount) {
        wishlistCount.textContent = wishlist.length;
    }
    
    // Save to localStorage only if logged in
    if (isUserLoggedIn()) {
        localStorage.setItem('radhi-wishlist', JSON.stringify(wishlist));
    }
    
    const wishlistBody = document.getElementById('wishlistBody');
    if (!wishlistBody) return;
    
    if (wishlist.length === 0) {
        wishlistBody.innerHTML = '<p class="empty-message">Your wishlist is empty</p>';
        return;
    }
    
    wishlistBody.innerHTML = wishlist.map(item => `
        <div class="wishlist-item">
            <img src="${item.image}" alt="${item.name}">
            <div class="item-details">
                <h4>${item.name}</h4>
                <p class="item-price">₹${item.price}</p>
            </div>
            <button class="remove-btn" onclick="removeFromWishlist('${item.id}')">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

// Update Quantity
function updateQuantity(id, change) {
    const item = cart.find(item => item.id === id);
    if (item) {
        const oldQty = item.qty;
        
        // Max 8 limit check
        if (change > 0 && item.qty >= 8) {
            showNotification('⚠️ Maximum 8 items allowed per product!');
            return;
        }
        
        item.qty += change;
        
        if (item.qty <= 0) {
            removeFromCart(id);
        } else {
            // Update inventory when quantity changes
            const inventory = JSON.parse(localStorage.getItem('radhi-inventory')) || {};
            const currentStock = inventory[id] || 0;
            
            if (change < 0) {
                // Decreasing cart quantity - increase stock
                inventory[id] = currentStock + Math.abs(change);
            } else {
                // Increasing cart quantity - decrease stock
                if (currentStock > 0) {
                    inventory[id] = currentStock - change;
                } else {
                    showNotification('⚠️ No more stock available!');
                    item.qty = oldQty; // Revert quantity
                    return;
                }
            }
            
            localStorage.setItem('radhi-inventory', JSON.stringify(inventory));
            updateStockDisplay(id, inventory[id]);
            updateCart();
        }
    }
}

// Remove from Cart - Simple version
function removeFromCart(id) {
    const item = cart.find(item => item.id === id);
    const quantity = item ? item.qty : 0;
    
    cart = cart.filter(item => item.id !== id);
    localStorage.setItem('radhi-cart', JSON.stringify(cart));
    updateCart();
    showNotification('🗑️ Item removed from cart');
    
    // Update database in background
    if (quantity > 0) {
        updateDatabaseStock(id, quantity);
    }
}

// Remove from Wishlist
function removeFromWishlist(id) {
    wishlist = wishlist.filter(item => item.id !== id);
    localStorage.setItem('radhi-wishlist', JSON.stringify(wishlist));
    const wishlistBtn = document.querySelector(`.wishlist-btn[data-id="${id}"]`);
    if (wishlistBtn) wishlistBtn.classList.remove('active');
    updateWishlist();
    showNotification('🗑️ Item removed from wishlist');
}

// Toggle Cart Sidebar
function toggleCartSidebar() {
    const cartSidebar = document.getElementById('cartSidebar');
    const overlay = document.getElementById('overlay');
    
    if (cartSidebar && overlay) {
        cartSidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}

// Toggle Wishlist Sidebar
function toggleWishlistSidebar() {
    const wishlistSidebar = document.getElementById('wishlistSidebar');
    const overlay = document.getElementById('overlay');
    
    if (wishlistSidebar && overlay) {
        wishlistSidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
    
    // Show notification when opening wishlist
    const wishlist = JSON.parse(localStorage.getItem('radhi-wishlist')) || [];
    if (wishlist.length === 0) {
        showNotification('Your wishlist is empty!');
    } else {
        showNotification(`You have ${wishlist.length} item${wishlist.length > 1 ? 's' : ''} in your wishlist`);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCart();
    updateWishlist();
    
    // Initialize inventory from product cards
    initializeInventory();
    
    // Mark wishlist items as active on page load
    const wishlist = JSON.parse(localStorage.getItem('radhi-wishlist')) || [];
    wishlist.forEach(item => {
        const productCard = document.querySelector(`.product-card[data-id="${item.id}"]`);
        if (productCard) {
            const wishlistBtn = productCard.querySelector('.wishlist-btn');
            if (wishlistBtn) {
                wishlistBtn.classList.add('active');
            }
        }
    });
    
    // Set up cart icon click
    const cartIcon = document.querySelector('.cart-icon');
    if (cartIcon) {
        cartIcon.addEventListener('click', toggleCartSidebar);
    }
    
    // Set up wishlist icon click
    const wishlistIcon = document.querySelector('.wishlist-icon');
    if (wishlistIcon) {
        wishlistIcon.addEventListener('click', toggleWishlistSidebar);
    }
});

// Initialize inventory from product cards on page
function initializeInventory() {
    const inventory = JSON.parse(localStorage.getItem('radhi-inventory')) || {};
    const productCards = document.querySelectorAll('.product-card[data-id]');
    
    productCards.forEach(card => {
        const productId = card.getAttribute('data-id');
        if (!inventory[productId]) {
            // First time - get stock from card
            const stockInfo = card.querySelector('.stock-info');
            if (stockInfo) {
                const match = stockInfo.textContent.match(/(\d+)\s*units?\s*available/i);
                if (match) {
                    inventory[productId] = parseInt(match[1]);
                }
            }
        } else {
            // Update display with saved inventory
            updateStockDisplay(productId, inventory[productId]);
        }
    });
    
    localStorage.setItem('radhi-inventory', JSON.stringify(inventory));
}

// Cross-tab synchronization - Listen for localStorage changes
window.addEventListener('storage', function(e) {
    // When cart or wishlist changes in another tab, update this tab
    if (e.key === 'radhi-cart') {
        cart = JSON.parse(e.newValue || '[]');
        updateCart();
        console.log('Cart updated from another tab:', cart.length, 'items');
    } else if (e.key === 'radhi-wishlist') {
        wishlist = JSON.parse(e.newValue || '[]');
        updateWishlist();
        console.log('Wishlist updated from another tab:', wishlist.length, 'items');
    }
});

// Product Filter
document.querySelectorAll('.filter-btn').forEach(button => {
    button.addEventListener('click', function() {
        document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
        
        const filter = this.dataset.filter;
        document.querySelectorAll('.product-card').forEach(card => {
            if (filter === 'all' || card.dataset.category === filter) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

// Smooth Scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Hero Navigation
const heroNav = document.querySelectorAll('.hero-nav');
const heroDots = document.querySelectorAll('.dot');

heroNav.forEach(nav => {
    nav.addEventListener('click', function() {
        showNotification('Slider navigation clicked!');
    });
});

heroDots.forEach((dot, index) => {
    dot.addEventListener('click', function() {
        heroDots.forEach(d => d.classList.remove('active'));
        this.classList.add('active');
    });
});

// Shop Now Button
const shopNowBtn = document.querySelector('.btn-shop-now');
if (shopNowBtn) {
    shopNowBtn.addEventListener('click', function() {
        const productsSection = document.getElementById('shop');
        if (productsSection) {
            productsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
}

// Notification Function
function showNotification(message) {
    // Remove existing notification if any
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: #7fad39;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        font-weight: 500;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize
console.log('Organico Grocery Store - Loaded Successfully!');
console.log('Cart:', cart);
console.log('Wishlist:', wishlist);
