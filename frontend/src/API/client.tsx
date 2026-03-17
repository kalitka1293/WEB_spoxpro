import axios, { AxiosInstance } from 'axios';

const API_BASE = 'http://localhost:8000'

// Создаем типизированный инстанс axios
export const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-type': 'application/json',
    },
});

apiClient.defaults.withCredentials = true; 

apiClient.interceptors.request.use((config) => {
  if (['post', 'put', 'delete'].includes(config.method || '')) {
    const token = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrf_token='))
      ?.split('=')[1];
    
    if (token) {
      config.headers['X-CSRF-Token'] = token;
    }
  }
  return config;
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: (v: any) => void; reject: (e: any) => void }> = [];

const processQueue = (error: any) => {
  failedQueue.forEach(p => (error ? p.reject(error) : p.resolve(undefined)));
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/user/check')) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => apiClient(originalRequest));
      }
      originalRequest._retry = true;
      isRefreshing = true;
      try {
        const { postRefreshToken } = await import('./RequestAPI');
        await postRefreshToken();
        processQueue(null);
        return apiClient(originalRequest);
      } catch (e) {
        processQueue(e);
        window.location.href = '/auth';
        return Promise.reject(e);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);
