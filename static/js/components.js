// Reusable UI components and utilities

class FormValidator {
    constructor(formElement) {
        this.form = formElement;
        this.rules = {};
        this.init();
    }
    
    init() {
        this.form.addEventListener('submit', (e) => this.validate(e));
    }
    
    addRule(fieldName, validatorFn, errorMessage) {
        if (!this.rules[fieldName]) {
            this.rules[fieldName] = [];
        }
        this.rules[fieldName].push({ validator: validatorFn, message: errorMessage });
    }
    
    validate(e) {
        let isValid = true;
        const formData = new FormData(this.form);
        
        // Clear previous errors
        this.clearErrors();
        
        // Validate each field with rules
        for (const [fieldName, validators] of Object.entries(this.rules)) {
            const value = formData.get(fieldName);
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            
            for (const rule of validators) {
                if (!rule.validator(value, formData)) {
                    this.showFieldError(field, rule.message);
                    isValid = false;
                    break;
                }
            }
        }
        
        if (!isValid) {
            e.preventDefault();
        }
        
        return isValid;
    }
    
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        // Insert after field
        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }
    
    clearErrors() {
        // Remove error classes
        this.form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        
        // Remove error messages
        this.form.querySelectorAll('.invalid-feedback').forEach(error => {
            error.remove();
        });
    }
}

// Common validation functions
const Validators = {
    required: (value) => value && value.trim() !== '',
    
    email: (value) => {
        if (!value) return true; // Optional field
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    
    numeric: (value) => {
        if (!value) return true; // Optional field
        return !isNaN(parseFloat(value)) && isFinite(value);
    },
    
    positiveNumber: (value) => {
        if (!value) return true; // Optional field
        const num = parseFloat(value);
        return !isNaN(num) && num > 0;
    },
    
    zipCode: (value) => {
        if (!value) return true; // Optional field
        return /^\d{5}(-\d{4})?$/.test(value);
    },
    
    dateOfBirth: (value) => {
        if (!value) return false;
        const date = new Date(value);
        const now = new Date();
        const age = (now - date) / (365.25 * 24 * 60 * 60 * 1000);
        return age >= 0 && age <= 120;
    },
    
    householdAges: (value) => {
        if (!value) return false;
        const ages = value.split(',').map(age => parseInt(age.trim()));
        return ages.every(age => age > 0 && age <= 120) && ages.length > 0;
    }
};

// Loading state manager
class LoadingManager {
    static show(element, text = 'Loading...') {
        if (!element) return;
        
        element.dataset.originalText = element.innerHTML;
        element.disabled = true;
        element.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </span>
            ${text}
        `;
    }
    
    static hide(element) {
        if (!element) return;
        
        element.disabled = false;
        element.innerHTML = element.dataset.originalText || element.innerHTML;
    }
}

// Currency formatter utility
class CurrencyFormatter {
    static format(amount, options = {}) {
        const defaults = {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        };
        
        return new Intl.NumberFormat('en-US', { ...defaults, ...options }).format(amount);
    }
    
    static formatCompact(amount) {
        if (amount >= 1000000) {
            return `$${(amount / 1000000).toFixed(1)}M`;
        } else if (amount >= 1000) {
            return `$${(amount / 1000).toFixed(1)}K`;
        }
        return this.format(amount);
    }
}

// Date formatter utility
class DateFormatter {
    static formatDate(date, options = {}) {
        const defaults = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        
        return new Date(date).toLocaleDateString('en-US', { ...defaults, ...options });
    }
    
    static formatDateTime(date) {
        return new Date(date).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }
    
    static timeAgo(date) {
        const now = new Date();
        const then = new Date(date);
        const diff = now - then;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 60) {
            return `${minutes} minutes ago`;
        } else if (hours < 24) {
            return `${hours} hours ago`;
        } else {
            return `${days} days ago`;
        }
    }
}

// Debounce utility for search inputs
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Storage utility for client-side caching
class StorageManager {
    static set(key, value, expireMinutes = 60) {
        const item = {
            value,
            expire: Date.now() + (expireMinutes * 60 * 1000)
        };
        localStorage.setItem(key, JSON.stringify(item));
    }
    
    static get(key) {
        const itemStr = localStorage.getItem(key);
        if (!itemStr) return null;
        
        const item = JSON.parse(itemStr);
        if (Date.now() > item.expire) {
            localStorage.removeItem(key);
            return null;
        }
        
        return item.value;
    }
    
    static remove(key) {
        localStorage.removeItem(key);
    }
    
    static clear() {
        localStorage.clear();
    }
}

// Export utilities for use in other scripts
window.FormValidator = FormValidator;
window.Validators = Validators;
window.LoadingManager = LoadingManager;
window.CurrencyFormatter = CurrencyFormatter;
window.DateFormatter = DateFormatter;
window.StorageManager = StorageManager;
window.debounce = debounce;
