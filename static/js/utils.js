/**
 * Personal Finance Manager Pro - Utility Functions
 * ================================================
 * 
 * Common utility functions used throughout the application
 * Including formatting, validation, and helper functions
 * 
 * Version: 1.0.0
 */

/**
 * Format currency amount
 */
export function formatCurrency(amount, currency = 'USD', locale = 'en-US') {
    if (typeof amount !== 'number' || isNaN(amount)) {
        return '$0.00';
    }
    
    try {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    } catch (error) {
        // Fallback formatting
        const symbol = getCurrencySymbol(currency);
        return `${symbol}${amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
    }
}

/**
 * Get currency symbol
 */
export function getCurrencySymbol(currency = 'USD') {
    const symbols = {
        USD: '$',
        EUR: '€',
        GBP: '£',
        JPY: '¥',
        CAD: 'C$',
        AUD: 'A$',
        INR: '₹',
        CNY: '¥',
        KRW: '₩',
        BRL: 'R$',
        MXN: '$',
        RUB: '₽'
    };
    
    return symbols[currency] || '$';
}

/**
 * Format date
 */
export function formatDate(date, format = 'short', locale = 'en-US') {
    if (!date) return '';
    
    let dateObj;
    if (typeof date === 'string') {
        dateObj = new Date(date);
    } else if (date instanceof Date) {
        dateObj = date;
    } else {
        return '';
    }
    
    if (isNaN(dateObj.getTime())) {
        return '';
    }
    
    const options = getDateFormatOptions(format);
    
    try {
        return new Intl.DateTimeFormat(locale, options).format(dateObj);
    } catch (error) {
        // Fallback formatting
        return dateObj.toLocaleDateString();
    }
}

/**
 * Get date format options
 */
function getDateFormatOptions(format) {
    const formats = {
        short: {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        },
        medium: {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        },
        long: {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric'
        },
        monthYear: {
            month: 'long',
            year: 'numeric'
        },
        relative: {} // Will be handled separately
    };
    
    return formats[format] || formats.short;
}

/**
 * Format relative date (e.g., "2 days ago")
 */
export function formatRelativeDate(date) {
    if (!date) return '';
    
    const dateObj = new Date(date);
    const now = new Date();
    const diffMs = now - dateObj;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) {
        return 'Just now';
    } else if (diffMinutes < 60) {
        return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays === 1) {
        return 'Yesterday';
    } else if (diffDays < 7) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        return `${weeks} week${weeks !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 365) {
        const months = Math.floor(diffDays / 30);
        return `${months} month${months !== 1 ? 's' : ''} ago`;
    } else {
        const years = Math.floor(diffDays / 365);
        return `${years} year${years !== 1 ? 's' : ''} ago`;
    }
}

/**
 * Format percentage
 */
export function formatPercentage(value, decimals = 1) {
    if (typeof value !== 'number' || isNaN(value)) {
        return '0%';
    }
    
    return `${value.toFixed(decimals)}%`;
}

/**
 * Format number with commas
 */
export function formatNumber(num, decimals = 0) {
    if (typeof num !== 'number' || isNaN(num)) {
        return '0';
    }
    
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Debounce function
 */
export function debounce(func, wait, immediate = false) {
    let timeout;
    
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(this, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(this, args);
    };
}

/**
 * Throttle function
 */
export function throttle(func, limit) {
    let inThrottle;
    
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Validate email address
 */
export function validateEmail(email) {
    if (!email || typeof email !== 'string') {
        return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email.trim().toLowerCase());
}

/**
 * Validate password strength
 */
export function validatePassword(password) {
    if (!password || typeof password !== 'string') {
        return false;
    }
    
    // At least 8 characters, contains letters and numbers
    return password.length >= 8 && 
           /[a-zA-Z]/.test(password) && 
           /[0-9]/.test(password);
}

/**
 * Validate username
 */
export function validateUsername(username) {
    if (!username || typeof username !== 'string') {
        return false;
    }
    
    // 3-50 characters, alphanumeric, underscore, hyphen
    const usernameRegex = /^[a-zA-Z0-9_-]{3,50}$/;
    return usernameRegex.test(username);
}

/**
 * Validate amount
 */
export function validateAmount(amount) {
    const num = parseFloat(amount);
    return !isNaN(num) && num > 0 && num <= 1000000;
}

/**
 * Sanitize HTML
 */
export function sanitizeHtml(str) {
    if (typeof str !== 'string') {
        return '';
    }
    
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

/**
 * Generate random ID
 */
export function generateId(prefix = '') {
    return prefix + Math.random().toString(36).substr(2, 9);
}

/**
 * Deep clone object
 */
export function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') {
        return obj;
    }
    
    if (obj instanceof Date) {
        return new Date(obj.getTime());
    }
    
    if (obj instanceof Array) {
        return obj.map(item => deepClone(item));
    }
    
    if (typeof obj === 'object') {
        const cloned = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                cloned[key] = deepClone(obj[key]);
            }
        }
        return cloned;
    }
    
    return obj;
}

/**
 * Check if object is empty
 */
export function isEmpty(obj) {
    if (obj === null || obj === undefined) {
        return true;
    }
    
    if (Array.isArray(obj) || typeof obj === 'string') {
        return obj.length === 0;
    }
    
    if (typeof obj === 'object') {
        return Object.keys(obj).length === 0;
    }
    
    return false;
}

/**
 * Calculate percentage change
 */
export function calculatePercentageChange(oldValue, newValue) {
    if (!oldValue || oldValue === 0) {
        return newValue > 0 ? 100 : 0;
    }
    
    return ((newValue - oldValue) / oldValue) * 100;
}

/**
 * Get date range for period
 */
export function getDateRange(period) {
    const now = new Date();
    let startDate, endDate;
    
    switch (period) {
        case 'today':
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            endDate = new Date(startDate);
            endDate.setDate(endDate.getDate() + 1);
            break;
            
        case 'yesterday':
            startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
            endDate = new Date(startDate);
            endDate.setDate(endDate.getDate() + 1);
            break;
            
        case 'this_week':
            const dayOfWeek = now.getDay();
            startDate = new Date(now);
            startDate.setDate(now.getDate() - dayOfWeek);
            endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 7);
            break;
            
        case 'last_week':
            const lastWeekDay = now.getDay();
            startDate = new Date(now);
            startDate.setDate(now.getDate() - lastWeekDay - 7);
            endDate = new Date(startDate);
            endDate.setDate(startDate.getDate() + 7);
            break;
            
        case 'this_month':
            startDate = new Date(now.getFullYear(), now.getMonth(), 1);
            endDate = new Date(now.getFullYear(), now.getMonth() + 1, 1);
            break;
            
        case 'last_month':
            startDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
            endDate = new Date(now.getFullYear(), now.getMonth(), 1);
            break;
            
        case 'this_year':
            startDate = new Date(now.getFullYear(), 0, 1);
            endDate = new Date(now.getFullYear() + 1, 0, 1);
            break;
            
        case 'last_year':
            startDate = new Date(now.getFullYear() - 1, 0, 1);
            endDate = new Date(now.getFullYear(), 0, 1);
            break;
            
        default:
            // Default to this month
            startDate = new Date(now.getFullYear(), now.getMonth(), 1);
            endDate = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    }
    
    return {
        start: startDate.toISOString().split('T')[0],
        end: new Date(endDate.getTime() - 1).toISOString().split('T')[0]
    };
}
/**
 * Show toast notification
 */
export function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'polite');
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-message">${sanitizeHtml(message)}</div>
        </div>
        <button class="toast-close" aria-label="Close notification">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    
    // Add close functionality
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => removeToast(toast));
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Show toast with animation
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => removeToast(toast), duration);
    }
    
    return toast;
}

/**
 * Create toast container
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'false');
    document.body.appendChild(container);
    return container;
}

/**
 * Remove toast notification
 */
function removeToast(toast) {
    if (toast && toast.parentNode) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

/**
 * Show confirmation dialog
 */
export function showConfirmation(message, title = 'Confirm Action') {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmation-modal');
        if (!modal) {
            resolve(false);
            return;
        }
        
        const titleElement = document.getElementById('confirm-title');
        const messageElement = document.getElementById('confirm-message');
        const proceedBtn = document.getElementById('confirm-proceed');
        const cancelBtn = document.getElementById('confirm-cancel');
        const overlay = document.getElementById('modal-overlay');
        
        if (titleElement) titleElement.textContent = title;
        if (messageElement) messageElement.textContent = message;
        
        // Show modal
        overlay.classList.add('active');
        modal.classList.add('active');
        overlay.style.display = 'flex';
        modal.style.display = 'block';
        
        // Handle buttons
        const handleProceed = () => {
            cleanup();
            resolve(true);
        };
        
        const handleCancel = () => {
            cleanup();
            resolve(false);
        };
        
        const cleanup = () => {
            overlay.classList.remove('active');
            modal.classList.remove('active');
            setTimeout(() => {
                overlay.style.display = 'none';
                modal.style.display = 'none';
            }, 300);
            
            proceedBtn.removeEventListener('click', handleProceed);
            cancelBtn.removeEventListener('click', handleCancel);
            document.removeEventListener('keydown', handleKeydown);
        };
        
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                handleCancel();
            } else if (e.key === 'Enter') {
                handleProceed();
            }
        };
        
        proceedBtn.addEventListener('click', handleProceed);
        cancelBtn.addEventListener('click', handleCancel);
        document.addEventListener('keydown', handleKeydown);
        
        // Focus the proceed button
        setTimeout(() => proceedBtn.focus(), 100);
    });
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            const success = document.execCommand('copy');
            textArea.remove();
            return success;
        }
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        return false;
    }
}

/**
 * Download data as file
 */
export function downloadFile(data, filename, type = 'text/plain') {
    const blob = new Blob([data], { type });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up the URL object
    setTimeout(() => URL.revokeObjectURL(url), 100);
}

/**
 * Format file size
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get device info
 */
export function getDeviceInfo() {
    const ua = navigator.userAgent;
    const isMobile = /Mobile|Android|iPhone|iPad/.test(ua);
    const isTablet = /iPad|Android(?!.*Mobile)/.test(ua);
    const isDesktop = !isMobile && !isTablet;
    
    return {
        isMobile,
        isTablet,
        isDesktop,
        userAgent: ua,
        language: navigator.language,
        platform: navigator.platform,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine
    };
}

/**
 * Check if element is in viewport
 */
export function isInViewport(element) {
    if (!element) return false;
    
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Smooth scroll to element
 */
export function scrollToElement(element, offset = 0) {
    if (!element) return;
    
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;
    
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

/**
 * Get query parameters from URL
 */
export function getQueryParams() {
    const params = {};
    const searchParams = new URLSearchParams(window.location.search);
    
    for (const [key, value] of searchParams) {
        params[key] = value;
    }
    
    return params;
}

/**
 * Set query parameters in URL
 */
export function setQueryParams(params) {
    const url = new URL(window.location);
    
    Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
            url.searchParams.set(key, params[key]);
        } else {
            url.searchParams.delete(key);
        }
    });
    
    window.history.replaceState({}, '', url);
}

/**
 * Format duration (seconds to human readable)
 */
export function formatDuration(seconds) {
    if (seconds < 60) {
        return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
    }
}

/**
 * Parse CSV data
 */
export function parseCSV(csvText, delimiter = ',') {
    const lines = csvText.split('\n');
    const result = [];
    const headers = lines[0].split(delimiter).map(header => header.trim().replace(/"/g, ''));
    
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const values = line.split(delimiter).map(value => value.trim().replace(/"/g, ''));
        const row = {};
        
        headers.forEach((header, index) => {
            row[header] = values[index] || '';
        });
        
        result.push(row);
    }
    
    return result;
}

/**
 * Convert data to CSV
 */
export function toCSV(data, headers = null) {
    if (!Array.isArray(data) || data.length === 0) {
        return '';
    }
    
    const csvHeaders = headers || Object.keys(data[0]);
    const csvRows = [csvHeaders.join(',')];
    
    data.forEach(row => {
        const values = csvHeaders.map(header => {
            const value = row[header] || '';
            // Escape quotes and wrap in quotes if contains comma or quote
            const stringValue = String(value);
            if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                return `"${stringValue.replace(/"/g, '""')}"`;
            }
            return stringValue;
        });
        csvRows.push(values.join(','));
    });
    
    return csvRows.join('\n');
}

/**
 * Generate color from string (for consistent colors)
 */
export function stringToColor(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 60%)`;
}

/**
 * Get contrast color (black or white) for background
 */
export function getContrastColor(backgroundColor) {
    // Convert hex to RGB
    let r, g, b;
    
    if (backgroundColor.startsWith('#')) {
        const hex = backgroundColor.substring(1);
        r = parseInt(hex.substr(0, 2), 16);
        g = parseInt(hex.substr(2, 2), 16);
        b = parseInt(hex.substr(4, 2), 16);
    } else if (backgroundColor.startsWith('rgb')) {
        const matches = backgroundColor.match(/\d+/g);
        r = parseInt(matches[0]);
        g = parseInt(matches[1]);
        b = parseInt(matches[2]);
    } else {
        return '#000000'; // Default to black
    }
    
    // Calculate luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    return luminance > 0.5 ? '#000000' : '#ffffff';
}

/**
 * Animate number counter
 */
export function animateCounter(element, start, end, duration = 1000, callback = null) {
    if (!element) return;
    
    const startTime = performance.now();
    const difference = end - start;
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease out cubic)
        const easeOutCubic = 1 - Math.pow(1 - progress, 3);
        const currentValue = start + (difference * easeOutCubic);
        
        element.textContent = Math.round(currentValue).toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        } else if (callback) {
            callback();
        }
    }
    
    requestAnimationFrame(updateCounter);
}

/**
 * Local storage helpers
 */
export const storage = {
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error writing to localStorage:', error);
            return false;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    },
    
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }
};

/**
 * Session storage helpers
 */
export const sessionStorage = {
    get(key, defaultValue = null) {
        try {
            const item = window.sessionStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from sessionStorage:', error);
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            window.sessionStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error writing to sessionStorage:', error);
            return false;
        }
    },
    
    remove(key) {
        try {
            window.sessionStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from sessionStorage:', error);
            return false;
        }
    },
    
    clear() {
        try {
            window.sessionStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing sessionStorage:', error);
            return false;
        }
    }
};

/**
 * Event emitter for custom events
 */
export class EventEmitter {
    constructor() {
        this.events = {};
    }
    
    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }
    
    off(event, callback) {
        if (!this.events[event]) return;
        
        const index = this.events[event].indexOf(callback);
        if (index > -1) {
            this.events[event].splice(index, 1);
        }
    }
    
    emit(event, ...args) {
        if (!this.events[event]) return;
        
        this.events[event].forEach(callback => {
            try {
                callback(...args);
            } catch (error) {
                console.error('Error in event callback:', error);
            }
        });
    }
    
    once(event, callback) {
        const onceCallback = (...args) => {
            callback(...args);
            this.off(event, onceCallback);
        };
        this.on(event, onceCallback);
    }
}

/**
 * Create a global event emitter instance
 */
export const eventBus = new EventEmitter();

/**
 * Performance measurement utilities
 */
export const performance = {
    mark(name) {
        if (window.performance && window.performance.mark) {
            window.performance.mark(name);
        }
    },
    
    measure(name, startMark, endMark) {
        if (window.performance && window.performance.measure) {
            try {
                window.performance.measure(name, startMark, endMark);
                const measure = window.performance.getEntriesByName(name)[0];
                return measure ? measure.duration : 0;
            } catch (error) {
                console.warn('Performance measurement failed:', error);
                return 0;
            }
        }
        return 0;
    },
    
    now() {
        return window.performance && window.performance.now ? 
               window.performance.now() : Date.now();
    }
};

/**
 * Initialize utility functions
 */
export function initUtils() {
    // Set up global error handling
    window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        // You could send this to an error reporting service
    });
    
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        // You could send this to an error reporting service
    });
    
    // Set up network status monitoring
    window.addEventListener('online', () => {
        showToast('Connection restored', 'success', 3000);
    });
    
    window.addEventListener('offline', () => {
        showToast('No internet connection', 'warning', 5000);
    });
    
    console.log('Utility functions initialized');
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUtils);
} else {
    initUtils();
}
