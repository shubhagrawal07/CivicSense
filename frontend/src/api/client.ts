import axios from "axios";
import { env } from "../config/env";
import { getStoredToken } from "../auth/tokenStorage";

export const client = axios.create({
  baseURL: env.apiBaseUrl,
});

// a wrong password is also a 401, so these two never carry the token
const OPEN_PATHS = ["/auth/login", "/auth/register"];

let onUnauthorized: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

client.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token && !OPEN_PATHS.includes(config.url ?? "")) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(undefined, (error) => {
  const sentToken = Boolean(error.config?.headers?.Authorization);
  if (error.response?.status === 401 && sentToken) {
    onUnauthorized?.();
  }
  return Promise.reject(error);
});
