// src/components/Navbar.jsx

import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Navbar.css";

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

        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#nav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div id="nav" className="collapse navbar-collapse">
          {user && (
            <ul className="navbar-nav me-auto">
              {/* Productos */}
              <li className="nav-item">
                <NavLink className="nav-link" to="/productos">
                  Productos
                </NavLink>
              </li>

              {/* Ventas */}
              <li className="nav-item dropdown">
                <a
                  className="nav-link dropdown-toggle"
                  href="#"
                  role="button"
                  data-bs-toggle="dropdown"
                >
                  Ventas
                </a>
                <ul className="dropdown-menu">
                  <li>
                    <NavLink className="dropdown-item" to="/ventas">
                      Punto de Venta
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className="dropdown-item" to="/ventas/historial">
                      Historial de Ventas
                    </NavLink>
                  </li>
                </ul>
              </li>

              {/* Compras (solo admin) */}
              {isAdmin && (
                <li className="nav-item dropdown">
                  <a
                    className="nav-link dropdown-toggle"
                    href="#"
                    role="button"
                    data-bs-toggle="dropdown"
                  >
                    Compras
                  </a>
                  <ul className="dropdown-menu">
                    <li>
                      <NavLink className="dropdown-item" to="/compras">
                        Ingreso de Compras
                      </NavLink>
                    </li>
                    <li>
                      <NavLink
                        className="dropdown-item"
                        to="/compras/historial"
                      >
                        Historial de Compras
                      </NavLink>
                    </li>
                  </ul>
                </li>
              )}

              {/* Dashboard */}
              <li className="nav-item">
                <NavLink className="nav-link" to="/dashboard">
                  Dashboard
                </NavLink>
              </li>
            </ul>
          )}

          {/* Usuario + Salir */}
          {user && (
            <div className="nav-user-box ms-auto">
              <span className="username-pill">{user.username}</span>
              <button
                className="btn-logout"
                type="button"
                onClick={handleLogout}
              >
                Salir
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
