// src/context/AuthContext.jsx

import { createContext, useContext, useEffect, useState } from "react";
import { login as loginService, logout as logoutService } from "../services/auth";
import { jwtDecode } from "jwt-decode"; // <-- 1. IMPORTAR LIBRERÍA

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // --- 2. FUNCIÓN PARA INICIALIZAR EL ESTADO DESDE EL TOKEN ---
  const initializeAuth = () => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      try {
        const decodedToken = jwtDecode(token);
        // Verificamos si el token ha expirado
        if (decodedToken.exp * 1000 > Date.now()) {
          setUser({
            username: decodedToken.username,
            groups: decodedToken.groups || [], // Guardamos los grupos
          });
        } else {
          // Si el token está expirado, limpiamos
          logoutService();
          setUser(null);
        }
      } catch (error) {
        console.error("Token inválido:", error);
        logoutService();
        setUser(null);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    initializeAuth();
  }, []);

  const login = async ({ username, password }) => {
    await loginService(username, password);
    // Después del login, reinicializamos el estado para leer el nuevo token
    initializeAuth();
  };

  const logout = () => {
    logoutService();
    setUser(null);
  };

  // --- 3. AÑADIMOS FUNCIONES HELPER PARA COMPROBAR ROLES ---
  const isAdmin = user?.groups.includes('Admin') || false;
  const isCajero = user?.groups.includes('Cajero') || false;

  return (
    <AuthContext.Provider value={{ user, login, logout, loading, isAdmin, isCajero }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}