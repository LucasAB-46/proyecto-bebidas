import Navbar from "../components/Navbar";

export default function Dashboard() {
  return (
    <>
      <Navbar />
      <div className="container py-4">
        <div className="card shadow-sm">
          <div className="card-body">
            <h4 className="mb-2" style={{ color: "var(--primary)" }}>Bienvenido</h4>
            <p className="text-muted m-0">Sistema de Gestión para Local de Bebidas — InnovaTI by LB</p>
          </div>
        </div>
      </div>
    </>
  );
}
