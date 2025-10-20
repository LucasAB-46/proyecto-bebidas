// src/api/client.jsx

import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

const api = axios.create({ baseURL });

const getAccess  = () => localStorage.getItem("accessToken");
const getRefresh = () => localStorage.getItem("refreshToken");
const setAccess  = (t) => t ? localStorage.setItem("accessToken", t) : localStorage.removeItem("accessToken");
const clearAuth  = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("user");
};

api.interceptors.request.use((config) => {
  const token = getAccess();
  if (token && !config.url.includes("/auth/token")) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  config.headers['X-Local-ID'] = '1';
  return config;
});

let refreshing = false;
let queue = [];
const flush = (err, token) => {
  queue.forEach(p => (err ? p.reject(err) : p.resolve(token)));
  queue = [];
};

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    const status = error?.response?.status;

    if (status !== 401 || original._retry) return Promise.reject(error);
    const refresh = getRefresh();
    if (!refresh) { clearAuth(); return Promise.reject(error); }

    if (refreshing) {
      return new Promise((resolve, reject) => queue.push({ resolve, reject }))
        .then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
    }

    original._retry = true;
    refreshing = true;
    try {
      const { data } = await axios.post(`${baseURL}/auth/refresh/`, { refresh });
      setAccess(data.access);
      flush(null, data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (e) {
      flush(e, null);
      clearAuth();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(e);
    } finally {
      refreshing = false;
    }
  }
);

export default api;