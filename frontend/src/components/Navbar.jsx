// src/components/Navbar.jsx

import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const nav = useNavigate();
  const { user, logout: authLogout, isAdmin } = useAuth();

  const handleLogout = () => {
    authLogout();
    nav("/login", { replace: true });
  };

  return (
    <nav className="navbar navbar-expand-lg bg-light border-bottom">
      <div className="container">
        <NavLink className="navbar-brand fw-bold text-danger" to="/productos">
          InnovaTI by LB
        </NavLink>

        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#nav">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div id="nav" className="collapse navbar-collapse">
          {/* Los links de navegación se muestran si hay un usuario */}
          {user && (
            <ul className="navbar-nav me-auto">
              <li className="nav-item"><NavLink className="nav-link" to="/productos">Productos</NavLink></li>
              <li className="nav-item"><NavLink className="nav-link" to="/ventas">Ventas</NavLink></li>
              {isAdmin && (
                <li className="nav-item"><NavLink className="nav-link" to="/compras">Compras</NavLink></li>
              )}
              <li className="nav-item">
                <a className="nav-link" href="/dashboard">Dashboard
                </a>
              </li>

            </ul>
          )}

          {/* --- INICIO DE LA CORRECCIÓN --- */}
          {/* El saludo y el botón de salir se muestran si hay un usuario, fuera de la lista de links */}
          {user && (
            <div className="d-flex align-items-center gap-3 ms-auto">
              <span className="text-muted small">{user.username}</span>
              <button className="btn btn-outline-secondary btn-sm" onClick={handleLogout}>
                Salir
              </button>
            </div>
          )}
          {/* --- FIN DE LA CORRECCIÓN --- */}
        </div>
      </div>
    </nav>
  );
}