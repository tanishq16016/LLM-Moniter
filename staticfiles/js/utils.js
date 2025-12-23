/**
 * LLM Monitor - Utility Functions
 * Common helper functions used across the dashboard
 */

// ============================================================
// Number Formatting
// ============================================================

/**
 * Format a number with K/M/B suffixes for large numbers
 * @param {number} num - The number to format
 * @param {number} decimals - Decimal places (default: 1)
 * @returns {string} Formatted number string
 */
function formatNumber(num, decimals = 1) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    
    num = Number(num);
    
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(decimals) + 'B';
    }
    if (num >= 1000000) {
        return (num / 1000000).toFixed(decimals) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(decimals) + 'K';
    }
    return num.toFixed(0);
}

/**
 * Format currency value
 * @param {number} amount - The amount to format
 * @param {number} decimals - Decimal places (default: 4)
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount, decimals = 4) {
    if (amount === null || amount === undefined || isNaN(amount)) return '$0.0000';
    return '$' + Number(amount).toFixed(decimals);
}

/**
 * Format percentage value
 * @param {number} value - The value to format
 * @param {number} decimals - Decimal places (default: 1)
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value, decimals = 1) {
    if (value === null || value === undefined || isNaN(value)) return '0%';
    return Number(value).toFixed(decimals) + '%';
}

/**
 * Format bytes to human readable string
 * @param {number} bytes - Number of bytes
 * @returns {string} Formatted string (e.g., "1.5 MB")
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}


// ============================================================
// Date/Time Formatting
// ============================================================

/**
 * Format ISO timestamp to readable format
 * @param {string} isoString - ISO timestamp string
 * @param {boolean} includeTime - Whether to include time (default: true)
 * @returns {string} Formatted date string
 */
function formatTimestamp(isoString, includeTime = true) {
    if (!isoString) return '-';
    
    const date = new Date(isoString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
        options.second = '2-digit';
    }
    
    return date.toLocaleDateString('en-US', options);
}

/**
 * Format timestamp to relative time (e.g., "2 hours ago")
 * @param {string} isoString - ISO timestamp string (UTC)
 * @returns {string} Relative time string
 */
function formatRelativeTime(isoString) {
    if (!isoString) return '-';
    
    // Parse the UTC timestamp correctly
    const date = new Date(isoString);
    const now = new Date();
    
    // Calculate difference in milliseconds
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHour < 24) return `${diffHour}h ago`;
    if (diffDay < 7) return `${diffDay}d ago`;
    
    return formatTimestamp(isoString, false);
}

/**
 * Format timestamp to exact local time
 * @param {string} isoString - ISO timestamp string (UTC)
 * @param {boolean} includeSeconds - Whether to include seconds (default: true)
 * @returns {string} Formatted local time string
 */
function formatExactTime(isoString, includeSeconds = true) {
    if (!isoString) return '-';
    
    const date = new Date(isoString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    
    if (includeSeconds) {
        options.second = '2-digit';
    }
    
    return date.toLocaleString('en-US', options);
}

/**
 * Format timestamp to date only (no time)
 * @param {string} isoString - ISO timestamp string (UTC)
 * @returns {string} Formatted date string
 */
function formatDate(isoString) {
    if (!isoString) return '-';
    
    const date = new Date(isoString);
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return date.toLocaleDateString('en-US', options);
}

/**
 * Format date for input[type="date"]
 * @param {Date} date - Date object
 * @returns {string} YYYY-MM-DD format
 */
function formatDateForInput(date) {
    return date.toISOString().split('T')[0];
}

/**
 * Get start of day for a date
 * @param {Date} date - Date object
 * @returns {Date} Date at 00:00:00
 */
function getStartOfDay(date) {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d;
}

/**
 * Get end of day for a date
 * @param {Date} date - Date object
 * @returns {Date} Date at 23:59:59
 */
function getEndOfDay(date) {
    const d = new Date(date);
    d.setHours(23, 59, 59, 999);
    return d;
}


// ============================================================
// String Utilities
// ============================================================

/**
 * Truncate string with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated string
 */
function truncateString(str, maxLength = 50) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.substring(0, maxLength - 3) + '...';
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Capitalize first letter of string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Extract model short name from full model ID
 * @param {string} modelName - Full model name (e.g., "llama-3.1-70b-versatile")
 * @returns {string} Short name (e.g., "70b-versatile")
 */
function getModelShortName(modelName) {
    if (!modelName) return 'Unknown';
    const parts = modelName.split('-');
    return parts.slice(-2).join('-');
}


// ============================================================
// Token Utilities
// ============================================================

/**
 * Estimate token count from text (rough approximation)
 * @param {string} text - Text to estimate
 * @returns {number} Estimated token count
 */
function estimateTokenCount(text) {
    if (!text) return 0;
    // Rough approximation: ~4 characters per token for English
    return Math.ceil(text.length / 4);
}

/**
 * Format token usage string
 * @param {number} input - Input tokens
 * @param {number} output - Output tokens
 * @returns {string} Formatted string (e.g., "150 / 250")
 */
function formatTokenUsage(input, output) {
    return `${formatNumber(input)} / ${formatNumber(output)}`;
}


// ============================================================
// Function Utilities
// ============================================================

/**
 * Debounce function execution
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function execution
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in ms
 * @returns {Function} Throttled function
 */
function throttle(func, limit = 300) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}


// ============================================================
// CSRF & API Utilities
// ============================================================

/**
 * Get CSRF token from cookies
 * @returns {string} CSRF token
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Make API request with proper headers
 * @param {string} url - Request URL
 * @param {object} options - Fetch options
 * @returns {Promise} Fetch promise
 */
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    const response = await fetch(url, mergedOptions);
    
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
    }
    
    return response.json();
}


// ============================================================
// Toast Notifications
// ============================================================

/**
 * Show toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'success', 'danger', 'warning', 'info'
 * @param {number} duration - Duration in ms (default: 3000)
 */
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const icons = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    };
    
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.id = toastId;
    
    toast.innerHTML = `
        <i class="bi ${icons[type]}"></i>
        <span>${escapeHtml(message)}</span>`;
    
    toastContainer.appendChild(toast);
    
    // Auto-hide after duration
    setTimeout(() => {
        toast.remove();
    }, duration);
}

/**
 * Create toast container if not exists
 * @returns {HTMLElement} Toast container element
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1100';
    document.body.appendChild(container);
    return container;
}


// ============================================================
// DOM Utilities
// ============================================================

/**
 * Create element with attributes and content
 * @param {string} tag - HTML tag name
 * @param {object} attrs - Attributes object
 * @param {string|HTMLElement|Array} content - Inner content
 * @returns {HTMLElement} Created element
 */
function createElement(tag, attrs = {}, content = null) {
    const el = document.createElement(tag);
    
    Object.entries(attrs).forEach(([key, value]) => {
        if (key === 'className') {
            el.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(el.style, value);
        } else if (key.startsWith('on') && typeof value === 'function') {
            el.addEventListener(key.substring(2).toLowerCase(), value);
        } else {
            el.setAttribute(key, value);
        }
    });
    
    if (content) {
        if (Array.isArray(content)) {
            content.forEach(c => {
                if (typeof c === 'string') {
                    el.appendChild(document.createTextNode(c));
                } else {
                    el.appendChild(c);
                }
            });
        } else if (typeof content === 'string') {
            el.innerHTML = content;
        } else {
            el.appendChild(content);
        }
    }
    
    return el;
}

/**
 * Show loading state on element
 * @param {HTMLElement} element - Element to show loading on
 * @param {string} text - Loading text (default: 'Loading...')
 */
function showLoading(element, text = 'Loading...') {
    element.dataset.originalContent = element.innerHTML;
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        ${text}
    `;
    element.disabled = true;
}

/**
 * Hide loading state and restore element
 * @param {HTMLElement} element - Element to restore
 */
function hideLoading(element) {
    if (element.dataset.originalContent) {
        element.innerHTML = element.dataset.originalContent;
        delete element.dataset.originalContent;
    }
    element.disabled = false;
}


// ============================================================
// Local Storage Utilities
// ============================================================

/**
 * Get item from localStorage with JSON parsing
 * @param {string} key - Storage key
 * @param {*} defaultValue - Default value if not found
 * @returns {*} Stored value or default
 */
function getStoredItem(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch {
        return defaultValue;
    }
}

/**
 * Set item in localStorage with JSON stringify
 * @param {string} key - Storage key
 * @param {*} value - Value to store
 */
function setStoredItem(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

/**
 * Remove item from localStorage
 * @param {string} key - Storage key
 */
function removeStoredItem(key) {
    localStorage.removeItem(key);
}


// ============================================================
// Chart.js Helpers
// ============================================================

/**
 * Create gradient for Chart.js
 * @param {CanvasRenderingContext2D} ctx - Canvas context
 * @param {string} color - Base color (hex or rgb)
 * @returns {CanvasGradient} Gradient object
 */
function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, color.includes('rgba') ? color : hexToRgba(color, 0.8));
    gradient.addColorStop(1, color.includes('rgba') ? color.replace(/[\d.]+\)$/, '0.1)') : hexToRgba(color, 0.1));
    return gradient;
}

/**
 * Convert hex color to rgba
 * @param {string} hex - Hex color
 * @param {number} alpha - Alpha value (0-1)
 * @returns {string} RGBA color string
 */
function hexToRgba(hex, alpha = 1) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return `rgba(0,0,0,${alpha})`;
    return `rgba(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}, ${alpha})`;
}


// ============================================================
// URL/Query Utilities
// ============================================================

/**
 * Build query string from object
 * @param {object} params - Parameters object
 * @returns {string} Query string
 */
function buildQueryString(params) {
    return Object.entries(params)
        .filter(([_, value]) => value !== null && value !== undefined && value !== '')
        .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
        .join('&');
}

/**
 * Parse query string to object
 * @param {string} queryString - Query string (with or without ?)
 * @returns {object} Parameters object
 */
function parseQueryString(queryString) {
    const params = {};
    const query = queryString.replace(/^\?/, '');
    if (!query) return params;
    
    query.split('&').forEach(pair => {
        const [key, value] = pair.split('=').map(decodeURIComponent);
        params[key] = value;
    });
    
    return params;
}


// ============================================================
// Validation Utilities
// ============================================================

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} Is valid email
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Check if string is valid JSON
 * @param {string} str - String to check
 * @returns {boolean} Is valid JSON
 */
function isValidJson(str) {
    try {
        JSON.parse(str);
        return true;
    } catch {
        return false;
    }
}

/**
 * Parse JSON safely with default value
 * @param {string} str - JSON string
 * @param {*} defaultValue - Default value on error
 * @returns {*} Parsed value or default
 */
function safeJsonParse(str, defaultValue = null) {
    try {
        return JSON.parse(str);
    } catch {
        return defaultValue;
    }
}


// ============================================================
// Export for module usage
// ============================================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatNumber,
        formatCurrency,
        formatPercentage,
        formatBytes,
        formatTimestamp,
        formatRelativeTime,
        formatDateForInput,
        truncateString,
        escapeHtml,
        capitalize,
        getModelShortName,
        estimateTokenCount,
        formatTokenUsage,
        debounce,
        throttle,
        getCsrfToken,
        apiRequest,
        showToast,
        createElement,
        showLoading,
        hideLoading,
        getStoredItem,
        setStoredItem,
        removeStoredItem,
        createGradient,
        hexToRgba,
        buildQueryString,
        parseQueryString,
        isValidEmail,
        isValidJson,
        safeJsonParse
    };
}
