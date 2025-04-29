import api from './config';

export const login = async (email, password) => {
    try {
        const response = await api.post('/usuarios/login/', {
            email,
            password
        });
        
        const { access, refresh, user } = response.data;
        
        // Guardar tokens en localStorage
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        localStorage.setItem('user', JSON.stringify(user));
        
        return { user };
    } catch (error) {
        throw error.response?.data || { error: 'Error al iniciar sesión' };
    }
};

export const register = async (userData) => {
    try {
        const response = await api.post('/usuarios/register/', userData);
        return response.data;
    } catch (error) {
        throw error.response?.data || { error: 'Error al registrar usuario' };
    }
};

export const logout = async () => {
    try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            await api.post('/usuarios/logout/', {
                refresh: refreshToken
            });
        }
        
        // Limpiar localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        
        return true;
    } catch (error) {
        // Aún así limpiamos el localStorage aunque falle la petición
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        throw error.response?.data || { error: 'Error al cerrar sesión' };
    }
};

export const getCurrentUser = () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
};

export const isAuthenticated = () => {
    return !!localStorage.getItem('access_token');
}; 