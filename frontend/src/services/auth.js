// src/services/auth.js
import api from "../api/client.jsx";

export async function login(username, password) {
  const { data } = await api.post("/auth/token/", { username, password });
  localStorage.setItem("accessToken", data.access);
  localStorage.setItem("refreshToken", data.refresh);
  localStorage.setItem("user", JSON.stringify({ username }));
  return data;
}

export function logout() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("user");
}