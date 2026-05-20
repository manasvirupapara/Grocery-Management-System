// API Configuration
const API_BASE_URL = 'http://127.0.0.1:8000/api';

const API_ENDPOINTS = {
    products: `${API_BASE_URL}/products/`,
    categories: `${API_BASE_URL}/categories/`,
    checkout: `${API_BASE_URL}/checkout/`,
    orderDetail: (orderId) => `${API_BASE_URL}/orders/${orderId}/`,
    searchProducts: (query) => `${API_BASE_URL}/products/search/?q=${encodeURIComponent(query)}`,
    productsByCategory: (categoryId) => `${API_BASE_URL}/products/by_category/?category=${categoryId}`,
};

// API Helper Functions
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Get all products
async function getProducts() {
    return await fetchAPI(API_ENDPOINTS.products);
}

// Get all categories
async function getCategories() {
    return await fetchAPI(API_ENDPOINTS.categories);
}

// Search products
async function searchProducts(query) {
    return await fetchAPI(API_ENDPOINTS.searchProducts(query));
}

// Get products by category
async function getProductsByCategory(categoryId) {
    return await fetchAPI(API_ENDPOINTS.productsByCategory(categoryId));
}

// Checkout
async function submitCheckout(checkoutData) {
    return await fetchAPI(API_ENDPOINTS.checkout, {
        method: 'POST',
        body: JSON.stringify(checkoutData),
    });
}

// Get order details
async function getOrderDetails(orderId) {
    return await fetchAPI(API_ENDPOINTS.orderDetail(orderId));
}
