/**
 * API Configuration
 * Change API_BASE_URL to point to your backend server
 */

// Get API_BASE_URL from window variable (set in HTML), or use default
const API_BASE_URL = window.API_CONFIG?.baseUrl || 'http://localhost:8000';

// Configuration object
const API_CONFIG = {
    baseUrl: API_BASE_URL,
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
    retryDelay: 1000
};
