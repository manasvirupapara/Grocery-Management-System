// Form Validation Utilities

// Validate name - only letters and spaces
function validateName(input) {
    const nameRegex = /^[a-zA-Z\s]+$/;
    return nameRegex.test(input);
}

// Validate mobile - only 10 digits
function validateMobile(input) {
    const mobileRegex = /^[0-9]{10}$/;
    return mobileRegex.test(input);
}

// Validate email
function validateEmail(input) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(input);
}

// Validate pincode - only 6 digits
function validatePincode(input) {
    const pincodeRegex = /^[0-9]{6}$/;
    return pincodeRegex.test(input);
}

// Validate numbers only
function validateNumbersOnly(input) {
    const numberRegex = /^[0-9]+$/;
    return numberRegex.test(input);
}

// Add real-time validation to input fields
function addInputValidation() {
    // Name fields - only letters and spaces
    document.querySelectorAll('input[type="text"][id*="name"], input[type="text"][id*="Name"], input[name*="name"], input[name*="Name"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            const char = String.fromCharCode(e.which);
            if (!/[a-zA-Z\s]/.test(char)) {
                e.preventDefault();
                showValidationError(this, 'Only letters and spaces allowed');
            }
        });
        
        input.addEventListener('input', function() {
            if (this.value && !validateName(this.value)) {
                this.value = this.value.replace(/[^a-zA-Z\s]/g, '');
            }
            clearValidationError(this);
        });
    });
    
    // Mobile fields - only numbers, max 10 digits
    document.querySelectorAll('input[type="tel"], input[id*="mobile"], input[id*="Mobile"], input[name*="mobile"], input[name*="phone"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            const char = String.fromCharCode(e.which);
            if (!/[0-9]/.test(char)) {
                e.preventDefault();
                showValidationError(this, 'Only numbers allowed');
            }
        });
        
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
            clearValidationError(this);
        });
    });
    
    // Email fields
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !validateEmail(this.value)) {
                showValidationError(this, 'Please enter a valid email address');
            } else {
                clearValidationError(this);
            }
        });
    });
    
    // Pincode fields - only numbers, max 6 digits
    document.querySelectorAll('input[id*="pincode"], input[id*="Pincode"], input[name*="pincode"], input[name*="zip"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            const char = String.fromCharCode(e.which);
            if (!/[0-9]/.test(char)) {
                e.preventDefault();
                showValidationError(this, 'Only numbers allowed');
            }
        });
        
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            if (this.value.length > 6) {
                this.value = this.value.slice(0, 6);
            }
            clearValidationError(this);
        });
    });
    
    // City and State fields - only letters and spaces
    document.querySelectorAll('input[id*="city"], input[id*="City"], input[id*="state"], input[id*="State"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            const char = String.fromCharCode(e.which);
            if (!/[a-zA-Z\s]/.test(char)) {
                e.preventDefault();
                showValidationError(this, 'Only letters and spaces allowed');
            }
        });
        
        input.addEventListener('input', function() {
            if (this.value) {
                this.value = this.value.replace(/[^a-zA-Z\s]/g, '');
            }
            clearValidationError(this);
        });
    });
}

// Show validation error
function showValidationError(input, message) {
    // Remove existing error
    clearValidationError(input);
    
    // Add error styling
    input.style.borderColor = '#dc3545';
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'validation-error';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '4px';
    errorDiv.textContent = message;
    
    // Insert error message after input
    input.parentNode.insertBefore(errorDiv, input.nextSibling);
    
    // Auto-hide after 3 seconds
    setTimeout(() => clearValidationError(input), 3000);
}

// Clear validation error
function clearValidationError(input) {
    input.style.borderColor = '';
    const errorDiv = input.parentNode.querySelector('.validation-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Validate form before submission
function validateForm(formElement) {
    let isValid = true;
    const inputs = formElement.querySelectorAll('input[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showValidationError(input, 'This field is required');
            isValid = false;
        } else {
            // Validate based on input type
            if (input.type === 'email' && !validateEmail(input.value)) {
                showValidationError(input, 'Please enter a valid email');
                isValid = false;
            } else if (input.type === 'tel' && !validateMobile(input.value)) {
                showValidationError(input, 'Please enter a valid 10-digit mobile number');
                isValid = false;
            } else if (input.id.includes('pincode') && !validatePincode(input.value)) {
                showValidationError(input, 'Please enter a valid 6-digit pincode');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

// Initialize validation on page load
document.addEventListener('DOMContentLoaded', function() {
    addInputValidation();
    
    // Add form submission validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                return false;
            }
        });
    });
});
