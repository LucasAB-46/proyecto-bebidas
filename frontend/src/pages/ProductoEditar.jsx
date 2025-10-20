/// src/pages/ProductoEditar.jsx
import { Link, useParams } from "react-router-dom";
import ProductoForm from "../components/ProductoForm.jsx"; // Asegúrate de que la importación sea correcta

export default function ProductoEditar() {
  const { id } = useParams();

  return (
    <div className="container py-3">
      <div className="d-flex align-items-center mb-3">
        <Link to="/productos" className="btn btn-light me-3">← Volver</Link>
        <h1 className="h4 mb-0">Editar Producto (ID: {id})</h1>
      </div>

      {/* --- LÍNEA AÑADIDA --- */}
      <ProductoForm />
      {/* --- FIN DE LA LÍNEA --- */}

    </div>
  );
}