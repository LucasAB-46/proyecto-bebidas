import axios from "axios";

const ROOT_API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: `${ROOT_API}/api`,
});

// -------- auth helpers --------
const getAccess  = () => localStorage.getItem("accessToken");
const getRefresh = () => localStorage.getItem("refreshToken");

const setAccess  = (t) => {
  if (t) {
    localStorage.setItem("accessToken", t);
  } else {
    localStorage.removeItem("accessToken");
  }
};

const clearAuth  = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("user");
};

// -------- request interceptor --------
api.interceptors.request.use((config) => {
  const token = getAccess();
  if (token && !config.url.includes("/auth/token")) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // MULTI-LOCAL 💥
  // leemos qué local eligió el usuario (lo guarda LocalContext en localStorage)
  const localId = localStorage.getItem("localActualId") || "1";
  config.headers["X-Local-ID"] = localId;

  return config;
});

// -------- refresh queue logic --------
let refreshing = false;
let queue = [];
const flush = (err, token) => {
  queue.forEach(p => (err ? p.reject(err) : p.resolve(token)));
  queue = [];
};

// -------- response interceptor --------
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const status = error?.response?.status;

    // si NO es 401 o ya reintentamos, soltamos el error
    if (status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    const refresh = getRefresh();
    if (!refresh) {
      clearAuth();
      return Promise.reject(error);
    }

    // si ya hay refresh en progreso, esperamos
    if (refreshing) {
      return new Promise((resolve, reject) => queue.push({ resolve, reject }))
        .then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
    }

    // empezamos un refresh nuevo
    original._retry = true;
    refreshing = true;
    try {
      const { data } = await axios.post(
        `${ROOT_API}/api/auth/refresh/`,
        { refresh }
      );

      setAccess(data.access);
      flush(null, data.access);

      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (e) {
      flush(e, null);
      clearAuth();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
      return Promise.reject(e);
    } finally {
      refreshing = false;
    }
  }
);

export default api;
