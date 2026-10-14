import axios from "axios";
import { env } from "../config/env";

export const client = axios.create({
  baseURL: env.apiBaseUrl,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("authToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
