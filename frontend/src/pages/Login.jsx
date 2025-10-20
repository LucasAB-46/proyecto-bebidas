// src/pages/Login.jsx

import { useAuth } from "../context/AuthContext";
import { useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";

export default function Login() {
  const nav = useNavigate();
  const location = useLocation();
  const { login } = useAuth(); // <-- Usamos la función login del contexto

  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Obtenemos la ruta a la que el usuario intentaba ir, si existe
  const from = location.state?.from?.pathname || "/productos";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const username = formData.get("username");
    const password = formData.get("password");

    try {
      await login({ username, password });
      // Si el login es exitoso, navegamos a la página de destino
      nav(from, { replace: true });
    } catch (err) {
      console.error("Error en el login:", err);
      setError("Credenciales incorrectas. Por favor, intente de nuevo.");
      setLoading(false);
    }
  };

  return (
    <div className="container d-flex justify-content-center align-items-center vh-100">
      <div className="card p-4" style={{ width: '100%', maxWidth: '400px' }}>
        <h1 className="h3 mb-3 text-center">Iniciar Sesión</h1>
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert-danger">{error}</div>}
          
          <div className="mb-3">
            <label htmlFor="username" className="form-label">Nombre de usuario</label>
            <input
              type="text"
              className="form-control"
              id="username"
              name="username"
              required
              autoFocus
            />
          </div>
          
          <div className="mb-3">
            <label htmlFor="password" className="form-label">Contraseña</label>
            <input
              type="password"
              className="form-control"
              id="password"
              name="password"
              required
            />
          </div>
          
          <div className="d-grid">
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Ingresando..." : "Login"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}