import React, { createContext, useState, useContext, useEffect } from 'react';
import { login as loginService, logout as logoutService, getCurrentUser, isAuthenticated } from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Verificar si hay un usuario autenticado al cargar la aplicación
        const checkAuth = () => {
            if (isAuthenticated()) {
                const currentUser = getCurrentUser();
                setUser(currentUser);
            }
            setLoading(false);
        };

        checkAuth();
    }, []);

    const login = async (email, password) => {
        try {
            const { user } = await loginService(email, password);
            setUser(user);
            return user;
        } catch (error) {
            throw error;
        }
    };

    const logout = async () => {
        try {
            await logoutService();
            setUser(null);
        } catch (error) {
            console.error('Error al cerrar sesión:', error);
            // Aún así limpiamos el estado local
            setUser(null);
        }
    };

    const value = {
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth debe ser usado dentro de un AuthProvider');
    }
    return context;
}; 