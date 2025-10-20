// src/components/ProductoForm.jsx

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom"; 
import { createProduct, listCategories, getProduct, updateProduct } from "../services/products";

export default function ProductoForm() {
  const nav = useNavigate();
  const { id } = useParams();
  const isEditing = !!id;

  const [categorias, setCategorias] = useState([]);
  const [formData, setFormData] = useState({
    codigo: "", nombre: "", marca: "", categoria: "", precio_venta: "", stock_actual: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true); // Empezamos en true para la carga inicial

  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    const loadInitialData = async () => {
      try {
        // Cargamos las categorías
        const categoriesRes = await listCategories();
        if (isMounted) {
          // La respuesta de DRF paginada tiene los resultados en .results
          setCategorias(categoriesRes.data.results || categoriesRes.data);
        }

        // Si estamos editando, cargamos los datos del producto
        if (isEditing) {
          const productRes = await getProduct(id);
          if (isMounted) {
            const product = productRes.data;
            setFormData({
              codigo: product.codigo,
              nombre: product.nombre,
              marca: product.marca || "",
              categoria: product.categoria,
              precio_venta: parseFloat(product.precio_venta).toFixed(2),
              stock_actual: parseInt(product.stock_actual),
            });
          }
        }
      } catch (err) {
        console.error("Error al cargar datos iniciales del formulario:", err);
        if (isMounted) {
          setError("No se pudo cargar la información necesaria para el formulario.");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadInitialData();

    return () => { isMounted = false; };
  }, [id, isEditing]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try {
      if (isEditing) {
        await updateProduct(id, formData);
        nav("/productos", { replace: true, state: { success: "Producto actualizado con éxito." } });
      } else {
        await createProduct(formData);
        nav("/productos", { replace: true, state: { success: "Producto creado con éxito." } });
      }
    } catch (err) {
      const errorData = err?.response?.data;
      if (errorData && typeof errorData === 'object') {
        const errorMessages = Object.entries(errorData).map(([key, value]) => `${key}: ${value.join(', ')}`).join('; ');
        setError(errorMessages);
      } else {
        setError(err?.response?.data?.detail || `Error al ${isEditing ? 'actualizar' : 'crear'} el producto.`);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="container py-3"><div className="spinner-border" role="status"><span className="visually-hidden">Cargando...</span></div></div>;
  }

  return (
    <div className="container py-3">
      <h1 className="h4 mb-3">{isEditing ? "Editar Producto" : "Crear Producto"}</h1>
      <form onSubmit={handleSubmit} className="card p-4">
        {error && <div className="alert alert-danger">{error}</div>}
        
        {/* El resto del JSX del formulario está perfecto y no necesita cambios */}
        <div className="mb-3">
          <label htmlFor="codigo" className="form-label">Código</label>
          <input type="text" className="form-control" id="codigo" name="codigo" value={formData.codigo} onChange={handleChange} required />
        </div>
        <div className="mb-3">
          <label htmlFor="nombre" className="form-label">Nombre</label>
          <input type="text" className="form-control" id="nombre" name="nombre" value={formData.nombre} onChange={handleChange} required />
        </div>
        <div className="mb-3">
          <label htmlFor="marca" className="form-label">Marca</label>
          <input type="text" className="form-control" id="marca" name="marca" value={formData.marca} onChange={handleChange} />
        </div>
        <div className="mb-3">
          <label htmlFor="categoria" className="form-label">Categoría</label>
          <select className="form-select" id="categoria" name="categoria" value={formData.categoria} onChange={handleChange} required>
            <option value="">Seleccione una categoría</option>
            {categorias.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.nombre}</option>
            ))}
          </select>
        </div>
        <div className="row">
          <div className="col-md-6 mb-3">
            <label htmlFor="precio_venta" className="form-label">Precio de Venta</label>
            <input type="number" step="0.01" className="form-control" id="precio_venta" name="precio_venta" value={formData.precio_venta} onChange={handleChange} required />
          </div>
          <div className="col-md-6 mb-3">
            <label htmlFor="stock_actual" className="form-label">Stock Actual</label>
            <input type="number" className="form-control" id="stock_actual" name="stock_actual" value={formData.stock_actual} onChange={handleChange} required />
          </div>
        </div>
        <div className="d-flex justify-content-end mt-3">
          <Link to="/productos" className="btn btn-secondary me-2">Cancelar</Link>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Guardando..." : `Guardar ${isEditing ? 'Cambios' : 'Producto'}`}
          </button>
        </div>
      </form>
    </div>
  );
}