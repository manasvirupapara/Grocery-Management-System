// Backend Integration for Radhi Fresh Mart
// This file replaces hardcoded products with API calls

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Global variables
let products = {}; // Will be populated from API
let categories = []; // Will be populated from API
// cart and wishlist are already declared in script.js

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadProductsFromAPI();
    await loadCategoriesFromAPI();
    loadCartFromLocalStorage();
    loadWishlistFromLocalStorage();
    updateCartCount();
    updateWishlistCount();
    checkUserSession();
    loadTheme();
    
    // Render products if on home page
    if (document.getElementById('productsGrid')) {
        renderProducts();
    }
});

// Load Products from Backend
async function loadProductsFromAPI() {
    try {
        const response = await fetch(`${API_BASE_URL}/products/`);
        if (!response.ok) throw new Error('Failed to fetch products');
        
        const data = await response.json();
        
        // Convert array to object with id as key (to match existing code structure)
        products = {};
        data.results.forEach(product => {
            products[product.id] = {
                id: product.id,
                name: product.name,
                price: parseFloat(product.selling_price),
                category: product.category_name ? product.category_name.toLowerCase() : 'other',
                image: product.image_url || 'https://via.placeholder.com/400',
                images: [
                    product.image_url || 'https://via.placeholder.com/400',
                    product.image_url || 'https://via.placeholder.com/400',
                    product.image_url || 'https://via.placeholder.com/400'
                ],
                stock: product.stock_quantity,
                sku: product.sku
            };
        });
        
        console.log('✅ Products loaded from backend:', Object.keys(products).length);
        return products;
    } catch (error) {
        console.error('❌ Error loading products:', error);
        showNotification('Failed to load products. Using offline mode.', 'error');
        // Fallback to hardcoded products if API fails
        loadFallbackProducts();
        return products;
    }
}

// Load Categories from Backend
async function loadCategoriesFromAPI() {
    try {
        const response = await fetch(`${API_BASE_URL}/categories/`);
        if (!response.ok) throw new Error('Failed to fetch categories');
        
        const data = await response.json();
        categories = data.results || data;
        
        console.log('✅ Categories loaded from backend:', categories.length);
        return categories;
    } catch (error) {
        console.error('❌ Error loading categories:', error);
        return [];
    }
}

// Search Products from Backend
async function searchProductsAPI(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/products/search/?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Search failed');
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('❌ Search error:', error);
        showNotification('Search failed. Please try again.', 'error');
        return [];
    }
}

// Render Products on Page
function renderProducts(filterCategory = 'all') {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;
    
    productsGrid.innerHTML = '';
    
    Object.values(products).forEach(product => {
        if (filterCategory !== 'all' && product.category !== filterCategory) {
            return;
        }
        
        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        productCard.dataset.category = product.category;
        
        const isInWishlist = wishlist.includes(product.id);
        const oldPrice = Math.round(product.price * 1.25);
        const discount = Math.round(((oldPrice - product.price) / oldPrice) * 100);
        
        productCard.innerHTML = `
            <div class="product-badge">-${discount}%</div>
            <button class="wishlist-btn ${isInWishlist ? 'active' : ''}" onclick="toggleWishlist(${product.id})">
                <i class="fas fa-heart"></i>
            </button>
            <div class="product-image" onclick="quickView(${product.id})">
                <img src="${product.image}" alt="${product.name}">
            </div>
            <div class="product-info">
                <span class="product-category">${product.category}</span>
                <h3 class="product-name">${product.name}</h3>
                <div class="product-rating">
                    <i class="fas fa-star"></i>
                    <i class="fas fa-star"></i>
                    <i class="fas fa-star"></i>
                    <i class="fas fa-star"></i>
                    <i class="fas fa-star-half-alt"></i>
                    <span>(4.5)</span>
                </div>
                <div class="product-price">
                    <span class="current-price">₹${product.price}</span>
                    <span class="old-price">₹${oldPrice}</span>
                </div>
                <button class="add-to-cart-btn" onclick="addToCart(${product.id})">
                    <i class="fas fa-shopping-cart"></i> Add to Cart
                </button>
            </div>
        `;
        
        productsGrid.appendChild(productCard);
    });
}

// Load Cart from localStorage
function loadCartFromLocalStorage() {
    const savedCart = localStorage.getItem('radhi-cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
    }
}

// Load Wishlist from localStorage
function loadWishlistFromLocalStorage() {
    const savedWishlist = localStorage.getItem('radhi-wishlist');
    if (savedWishlist) {
        wishlist = JSON.parse(savedWishlist);
    }
}

// Save Cart to localStorage
function saveCartToLocalStorage() {
    localStorage.setItem('radhi-cart', JSON.stringify(cart));
}

// Save Wishlist to localStorage
function saveWishlistToLocalStorage() {
    localStorage.setItem('radhi-wishlist', JSON.stringify(wishlist));
}

// Checkout Function - Submit to Backend
async function submitCheckout(formData) {
    try {
        // Prepare cart items for backend
        const cartItems = cart.map(item => ({
            product_id: item.id,
            quantity: item.qty
        }));
        
        const checkoutData = {
            customer_name: formData.name,
            customer_email: formData.email,
            customer_phone: formData.phone,
            customer_location: formData.address,
            customer_gender: formData.gender || 'Male',
            payment_method: formData.paymentMethod || 'COD',
            cart_items: cartItems
        };
        
        const response = await fetch(`${API_BASE_URL}/checkout/`, {
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
            cart = [];
            saveCartToLocalStorage();
            updateCartCount();
            
            // Redirect to success page
            window.location.href = `radhi-order-success.html?order_id=${result.order_id}`;
        } else {
            throw new Error(result.message || 'Checkout failed');
        }
        
    } catch (error) {
        console.error('❌ Checkout error:', error);
        showNotification(error.message || 'Checkout failed. Please try again.', 'error');
        throw error;
    }
}

// Get Order Details
async function getOrderDetails(orderId) {
    try {
        const response = await fetch(`${API_BASE_URL}/orders/${orderId}/`);
        if (!response.ok) throw new Error('Failed to fetch order details');
        
        const orderData = await response.json();
        return orderData;
    } catch (error) {
        console.error('❌ Error fetching order:', error);
        showNotification('Failed to load order details.', 'error');
        return null;
    }
}

// Fallback products (if API fails)
function loadFallbackProducts() {
    products = {
        1: { id: 1, name: 'Fresh Tomatoes', price: 45, category: 'vegetables', image: 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400&h=400&fit=crop', images: ['https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400&h=400&fit=crop', 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400&h=400&fit=crop', 'https://images.unsplash.com/photo-1546470427-e26264be0b0d?w=400&h=400&fit=crop'] },
        2: { id: 2, name: 'Organic Carrots', price: 38, category: 'vegetables', image: 'https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=400&h=400&fit=crop', images: ['https://images.unsplash.com/photo-1587735243615-c03f25aaff15?w=400&h=400&fit=crop', 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400&h=400&fit=crop', 'https://images.unsplash.com/photo-1445282768818-728615cc910a?w=400&h=400&fit=crop'] },
        3: { id: 3, name: 'Red Apples', price: 125, category: 'fruits', image: 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=400&fit=crop', images: ['https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=400&fit=crop', 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&h=400&fit=crop', 'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=400&h=400&fit=crop'] },
    };
}

console.log('🔌 Backend Integration Loaded - Radhi Fresh Mart');
