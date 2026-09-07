import axios from 'axios';

// FastAPI backend base URL'i (Dinamik Hostname Çözümleme)
const getBaseUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (typeof window !== 'undefined' && window.location.hostname && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

export const apiClient = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Response Interceptor: Backend'den gelen hataları merkezi formatla
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let errorMessage = 'Bilinmeyen bir hata oluştu.';

    if (error.response) {
      const data = error.response.data;
      if (typeof data?.detail === 'string') {
        errorMessage = data.detail;
      } else if (Array.isArray(data?.detail)) {
        // Pydantic validation error array
        errorMessage = data.detail.map((d: any) => `${d.loc?.slice(-1)[0] || 'Alan'}: ${d.msg}`).join(', ');
      } else if (error.response.status === 404) {
        errorMessage = 'İstenen kaynak bulunamadı (404).';
      } else if (error.response.status === 409) {
        errorMessage = 'Kayıt çakışması (409 Conflict).';
      } else if (error.response.status === 500) {
        errorMessage = 'Sunucu hatası oluştu (500).';
      }
    } else if (error.request) {
      errorMessage = 'Sunucuya bağlanılamadı. FastAPI sunucusunun açık olduğundan emin olun.';
    }

    return Promise.reject(new Error(errorMessage));
  }
);
