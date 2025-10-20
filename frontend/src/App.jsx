// src/App.jsx 

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Login from "./pages/Login.jsx";
import Productos from "./pages/Productos.jsx";
import Ventas from "./pages/Ventas.jsx";
import Compras from "./pages/Compras.jsx";
import ProductoNuevo from "./pages/ProductoNuevo.jsx";
import ProductoEditar from "./pages/ProductoEditar.jsx";
import { LocalProvider } from "./context/LocalContext.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import PrivateRoute from "./routes/PrivateRoute.jsx";
// La función RequireAuth ya no es necesaria, la hemos reemplazado por el componente PrivateRoute.

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <LocalProvider>
          <Navbar />

          <Routes>
            {/* Home: redirige al listado */}
            <Route path="/" element={<Navigate to="/productos" replace />} />

            {/* Pública */}
            <Route path="/login" element={<Login />} />

            {/* Privadas (ahora usando PrivateRoute) */}
            <Route
              path="/productos"
              element={
                <PrivateRoute>
                  <Productos />
                </PrivateRoute>
              }
            />
            <Route
              path="/ventas"
              element={
                <PrivateRoute>
                  <Ventas />
                </PrivateRoute>
              }
            />
            <Route
              path="/compras"
              element={
                <PrivateRoute>
                  <Compras />
                </PrivateRoute>
              }
            />
            <Route
              path="/productos/nuevo"
              element={
                <PrivateRoute>
                  <ProductoNuevo />
                </PrivateRoute>
              }
            />
            <Route
              path="/productos/:id/editar"
              element={
                <PrivateRoute>
                  <ProductoEditar />
                </PrivateRoute>
              }
            />

            {/* 404 */}
            <Route path="*" element={<div className="container p-4">404 – Página no encontrada</div>} />
          </Routes>
        </LocalProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}