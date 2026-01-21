// In production, VITE_API_BASE_URL should be empty string to use relative paths
// In development, it defaults to http://localhost:8011
// Check if VITE_API_BASE_URL is explicitly set (including empty string for production)
const envApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
export const API_BASE_URL = envApiBaseUrl !== undefined ? envApiBaseUrl : 'http://localhost:8011';

export const TOKEN_KEY = 'token';
