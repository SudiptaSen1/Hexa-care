// API Configuration
export const API_BASE = 'https://ea00-45-64-237-226.ngrok-free.app';

// API endpoints
export const API_ENDPOINTS = {
  // Auth endpoints
  AUTH: {
    SIGNUP: '/api/auth/signup',
    SIGNIN: '/api/auth/signin',
    USER: '/api/auth/user'
  },
  
  // Upload endpoints
  UPLOAD: {
    PRESCRIPTION: '/api/upload/upload-prescription',
    FILE: '/api/upload/upload'
  },
  
  // Chat endpoints
  CHAT: {
    START_SESSION: '/api/chat/sessions/start',
    SEND_MESSAGE: '/api/chat/sessions',
    GET_HISTORY: '/api/chat/history',
    GET_SESSIONS: '/api/chat/sessions'
  },
  
  // Prescription endpoints
  PRESCRIPTIONS: {
    UPLOAD: '/api/prescriptions/upload-prescription',
    GET_USER: '/api/prescriptions/prescriptions',
    GET_ACTIVE: '/api/prescriptions/active-medications',
    DELETE: '/api/prescriptions/prescription'
  },
  
  // Medication endpoints
  MEDICATIONS: {
    ADHERENCE: '/api/medications/medication-adherence',
    CONFIRMATIONS: '/api/medications/medication-confirmations',
    STATUS: '/api/medications/medication-status',
    RESPONSE: '/api/medications/medication-response'
  }
};

// Helper function to make API calls with proper headers
export const apiCall = async (endpoint, options = {}) => {
  const url = `${API_BASE}${endpoint}`;
  const defaultHeaders = {
    'ngrok-skip-browser-warning': 'true',
    'Content-Type': 'application/json',
  };

  // Get user ID from localStorage if available
  const userData = localStorage.getItem('userData');
  if (userData) {
    const user = JSON.parse(userData);
    defaultHeaders['X-User-ID'] = user.user_id;
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'API call failed');
    }
    
    return data;
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
};