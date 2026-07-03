import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
let accessToken = null;
let unauthorizedHandler = null;

export const apiClient = axios.create({ baseURL });

export function setAccessToken(token) {
  accessToken = token;
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && unauthorizedHandler) {
      unauthorizedHandler();
    }
    return Promise.reject(error);
  },
);

export function normalisePage(data) {
  return {
    items: data?.results ?? data ?? [],
    count: data?.count ?? (Array.isArray(data) ? data.length : 0),
    next: data?.next ?? null,
    previous: data?.previous ?? null,
  };
}
