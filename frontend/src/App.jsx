import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Login from "./pages/Login.jsx";
import Productos from "./pages/Productos.jsx";
import Ventas from "./pages/Ventas.jsx";
import Compras from "./pages/Compras.jsx";
import HistorialVentas from "./pages/HistorialVentas.jsx";
import HistorialCompras from "./pages/HistorialCompras.jsx";
import ProductoNuevo from "./pages/ProductoNuevo.jsx";
import ProductoEditar from "./pages/ProductoEditar.jsx";

import { LocalProvider } from "./context/LocalContext.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import PrivateRoute from "./routes/PrivateRoute.jsx";

export default function App() {
  return (
    <AuthProvider>
      <LocalProvider>
        <BrowserRouter>
          <Navbar />

          <Routes>
            {/* público */}
            <Route path="/login" element={<Login />} />

            {/* privado */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Navigate to="/productos" />
                </PrivateRoute>
              }
            />

            <Route
              path="/productos"
              element={
                <PrivateRoute>
                  <Productos />
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

            <Route
              path="/ventas"
              element={
                <PrivateRoute>
                  <Ventas />
                </PrivateRoute>
              }
            />

            <Route
              path="/ventas/historial"
              element={
                <PrivateRoute>
                  <HistorialVentas />
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
              path="/compras/historial"
              element={
                <PrivateRoute>
                  <HistorialCompras />
                </PrivateRoute>
              }
            />

            {/* fallback */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </BrowserRouter>
      </LocalProvider>
    </AuthProvider>
  );
}
