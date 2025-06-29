import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiCall, API_ENDPOINTS } from '../config/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on app start
    const userData = localStorage.getItem('userData');
    if (userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    try {
      const response = await apiCall(API_ENDPOINTS.AUTH.SIGNIN, {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      
      setUser(response);
      localStorage.setItem('userData', JSON.stringify(response));
      return response;
    } catch (error) {
      throw error;
    }
  };

  const signup = async (userData) => {
    try {
      const response = await apiCall(API_ENDPOINTS.AUTH.SIGNUP, {
        method: 'POST',
        body: JSON.stringify(userData),
      });
      
      setUser(response);
      localStorage.setItem('userData', JSON.stringify(response));
      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('userData');
  };

  const value = {
    user,
    login,
    signup,
    logout,
    loading,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};