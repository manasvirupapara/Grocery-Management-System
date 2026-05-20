// Toggle User Dropdown
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('active');
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const userMenu = document.getElementById('userMenu');
    const dropdown = document.getElementById('userDropdown');
    
    if (userMenu && dropdown && !userMenu.contains(e.target)) {
        dropdown.classList.remove('active');
    }
});

// Check User Session and Load User Info
function checkUserSession() {
    const user = JSON.parse(localStorage.getItem('radhi-user'));
    const userInfo = document.getElementById('userInfo');
    
    if (!userInfo) return;
    
    if (user && user.loggedIn) {
        // User is logged in
        userInfo.innerHTML = `
            <div class="user-profile-header">
                <div class="user-avatar">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="user-details">
                    <div class="user-name">${user.name || 'User'}</div>
                    <div class="user-email">${user.email || user.mobile || ''}</div>
                </div>
            </div>
            <div class="user-menu-divider"></div>
            <ul class="user-menu-list">
                <li><a href="radhi-profile.html"><i class="fas fa-user"></i> My Profile</a></li>
                <li><a href="radhi-cart.html"><i class="fas fa-shopping-bag"></i> My Orders</a></li>
                <li><a href="radhi-wishlist.html"><i class="fas fa-heart"></i> Wishlist</a></li>
                <li><a href="radhi-settings.html"><i class="fas fa-cog"></i> Settings</a></li>
            </ul>
            <div class="user-menu-divider"></div>
            <button class="logout-btn" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i> Logout
            </button>
        `;
    } else {
        // User is not logged in
        userInfo.innerHTML = `
            <div class="user-guest-header">
                <div class="user-avatar">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="user-details">
                    <div class="user-name">Welcome, Guest!</div>
                    <div class="user-subtitle">Login to access your account</div>
                </div>
            </div>
            <div class="user-menu-divider"></div>
            <a href="radhi-auth.html" class="login-btn">
                <i class="fas fa-sign-in-alt"></i> Login / Sign Up
            </a>
        `;
    }
}

// Logout Function
function logout() {
    localStorage.removeItem('radhi-user');
    showNotification('Logged out successfully! 👋', 'success');
    setTimeout(() => {
        window.location.href = 'radhi.html';
    }, 1000);
}

// Show Notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkUserSession();
});


// Delivery Address Functions
function openAddressModal() {
    // Check if modal already exists
    let modal = document.getElementById('deliveryAddressModal');
    
    if (!modal) {
        // Create modal
        modal = document.createElement('div');
        modal.id = 'deliveryAddressModal';
        modal.className = 'address-modal-overlay';
        modal.innerHTML = `
            <div class="address-modal-content">
                <div class="address-modal-header">
                    <h2><i class="fas fa-map-marker-alt"></i> Select Delivery Location</h2>
                    <button class="close-address-modal" onclick="closeAddressModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="address-modal-body">
                    <!-- Current Location Button -->
                    <button class="use-current-location-btn" onclick="useCurrentLocation()">
                        <i class="fas fa-crosshairs"></i>
                        <div>
                            <strong>Use Current Location</strong>
                            <span>Enable location to get accurate delivery time</span>
                        </div>
                    </button>
                    
                    <!-- Saved Addresses -->
                    <div class="saved-addresses-section">
                        <h3>Saved Addresses</h3>
                        <div id="savedAddressesList"></div>
                    </div>
                    
                    <!-- Add New Address -->
                    <div class="add-address-section">
                        <button class="add-new-address-btn" onclick="showAddAddressForm()">
                            <i class="fas fa-plus"></i> Add New Address
                        </button>
                        
                        <div id="addAddressForm" style="display: none;">
                            <h3>Add New Address</h3>
                            <form onsubmit="saveNewAddress(event)">
                                <div class="form-row">
                                    <input type="text" id="newHouse" placeholder="House / Flat / Block No." required>
                                    <input type="text" id="newApartment" placeholder="Apartment / Road / Area" required>
                                </div>
                                <div class="form-row">
                                    <input type="text" id="newLandmark" placeholder="Landmark (Optional)">
                                    <input type="text" id="newCity" placeholder="City" required>
                                </div>
                                <input type="text" id="newPincode" placeholder="Pincode" maxlength="6" required>
                                
                                <div class="address-type-selector">
                                    <label>Save as:</label>
                                    <div class="address-type-buttons">
                                        <button type="button" class="address-type-btn active" data-type="Home">
                                            <i class="fas fa-home"></i> Home
                                        </button>
                                        <button type="button" class="address-type-btn" data-type="Work">
                                            <i class="fas fa-briefcase"></i> Work
                                        </button>
                                        <button type="button" class="address-type-btn" data-type="Other">
                                            <i class="fas fa-map-marker-alt"></i> Other
                                        </button>
                                    </div>
                                </div>
                                
                                <div class="form-buttons">
                                    <button type="button" class="cancel-btn" onclick="hideAddAddressForm()">Cancel</button>
                                    <button type="submit" class="save-btn">Save Address</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Add event listeners for address type buttons
        setTimeout(() => {
            document.querySelectorAll('.address-type-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    document.querySelectorAll('.address-type-btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        }, 100);
    }
    
    // Load saved addresses
    loadSavedAddresses();
    
    // Show modal
    modal.classList.add('active');
}

function closeAddressModal() {
    const modal = document.getElementById('deliveryAddressModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function loadSavedAddresses() {
    const addresses = JSON.parse(localStorage.getItem('radhi-saved-addresses') || '[]');
    const currentAddress = JSON.parse(localStorage.getItem('radhi-delivery-address') || 'null');
    const listContainer = document.getElementById('savedAddressesList');
    
    if (addresses.length === 0) {
        listContainer.innerHTML = '<p class="no-addresses">No saved addresses yet</p>';
        return;
    }
    
    listContainer.innerHTML = addresses.map((addr, index) => `
        <div class="saved-address-item ${currentAddress && currentAddress.house === addr.house ? 'selected' : ''}" onclick="selectAddress(${index})">
            <div class="address-type-icon">
                <i class="fas fa-${addr.type === 'Home' ? 'home' : addr.type === 'Work' ? 'briefcase' : 'map-marker-alt'}"></i>
            </div>
            <div class="address-details">
                <strong>${addr.type}</strong>
                <p>${addr.house}, ${addr.apartment}</p>
                <p>${addr.landmark ? addr.landmark + ', ' : ''}${addr.city} - ${addr.pincode}</p>
            </div>
            ${currentAddress && currentAddress.house === addr.house ? '<i class="fas fa-check-circle selected-icon"></i>' : ''}
        </div>
    `).join('');
}

function selectAddress(index) {
    const addresses = JSON.parse(localStorage.getItem('radhi-saved-addresses') || '[]');
    const selectedAddress = addresses[index];
    
    // Save as current delivery address
    localStorage.setItem('radhi-delivery-address', JSON.stringify(selectedAddress));
    
    // Update navbar display
    updateNavbarAddress();
    
    // Close modal
    closeAddressModal();
    
    showNotification('✅ Delivery address updated!', 'success');
}

function updateNavbarAddress() {
    const address = JSON.parse(localStorage.getItem('radhi-delivery-address') || 'null');
    const navbarAddress = document.getElementById('navbarDeliveryAddress');
    
    if (address && navbarAddress) {
        navbarAddress.textContent = `${address.type} - ${address.city}, ${address.pincode}`;
    } else if (navbarAddress) {
        navbarAddress.textContent = 'Select delivery location';
    }
}

function showAddAddressForm() {
    document.getElementById('addAddressForm').style.display = 'block';
    document.querySelector('.add-new-address-btn').style.display = 'none';
}

function hideAddAddressForm() {
    document.getElementById('addAddressForm').style.display = 'none';
    document.querySelector('.add-new-address-btn').style.display = 'block';
    
    // Clear form
    document.getElementById('newHouse').value = '';
    document.getElementById('newApartment').value = '';
    document.getElementById('newLandmark').value = '';
    document.getElementById('newCity').value = '';
    document.getElementById('newPincode').value = '';
}

function saveNewAddress(e) {
    e.preventDefault();
    
    const newAddress = {
        house: document.getElementById('newHouse').value,
        apartment: document.getElementById('newApartment').value,
        landmark: document.getElementById('newLandmark').value,
        city: document.getElementById('newCity').value,
        pincode: document.getElementById('newPincode').value,
        type: document.querySelector('.address-type-btn.active').dataset.type
    };
    
    // Get existing addresses
    const addresses = JSON.parse(localStorage.getItem('radhi-saved-addresses') || '[]');
    
    // Add new address
    addresses.push(newAddress);
    
    // Save to localStorage
    localStorage.setItem('radhi-saved-addresses', JSON.stringify(addresses));
    
    // Set as current delivery address
    localStorage.setItem('radhi-delivery-address', JSON.stringify(newAddress));
    
    // Update navbar
    updateNavbarAddress();
    
    // Reload addresses list
    loadSavedAddresses();
    
    // Hide form
    hideAddAddressForm();
    
    showNotification('✅ Address saved successfully!', 'success');
}

function useCurrentLocation() {
    if (navigator.geolocation) {
        showNotification('📍 Getting your location...', 'info');
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                // In real app, you would reverse geocode to get address
                // For now, we'll show a placeholder
                const currentLocationAddress = {
                    house: 'Current Location',
                    apartment: `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`,
                    landmark: '',
                    city: 'Your City',
                    pincode: '000000',
                    type: 'Current'
                };
                
                localStorage.setItem('radhi-delivery-address', JSON.stringify(currentLocationAddress));
                updateNavbarAddress();
                closeAddressModal();
                
                showNotification('✅ Location detected!', 'success');
            },
            (error) => {
                showNotification('❌ Unable to get location. Please enable location services.', 'error');
            }
        );
    } else {
        showNotification('❌ Geolocation is not supported by your browser.', 'error');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkUserSession();
    updateNavbarAddress();
});


// Navbar Search Functions
function handleNavbarSearch(event) {
    if (event.key === 'Enter') {
        performNavbarSearch();
    }
}

function performNavbarSearch() {
    const searchBox = document.getElementById('navbarSearchBox');
    const query = searchBox.value.trim();
    
    if (query) {
        // Redirect to search page with query
        window.location.href = `radhi-search.html?q=${encodeURIComponent(query)}`;
    } else {
        alert('⚠️ Please enter a search term');
    }
}
