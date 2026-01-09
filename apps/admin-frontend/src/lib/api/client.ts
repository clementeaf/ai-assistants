import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface ApiError {
  message: string;
  status: number;
  code?: string;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const apiKey = this.getApiKey();
        if (apiKey && config.headers) {
          config.headers['X-API-Key'] = apiKey;
        }
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(this.handleError(error));
      }
    );

    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error: AxiosError) => {
        return Promise.reject(this.handleError(error));
      }
    );
  }

  private getApiKey(): string | null {
    return localStorage.getItem('api_key') || null;
  }

  private handleError(error: AxiosError): ApiError {
    if (error.response) {
      return {
        message: (error.response.data as { detail?: string })?.detail || error.message,
        status: error.response.status,
        code: error.code,
      };
    }
    if (error.request) {
      return {
        message: 'No se pudo conectar con el servidor',
        status: 0,
        code: error.code,
      };
    }
    return {
      message: error.message || 'Error desconocido',
      status: 0,
      code: error.code,
    };
  }

  setApiKey(apiKey: string): void {
    localStorage.setItem('api_key', apiKey);
  }

  clearApiKey(): void {
    localStorage.removeItem('api_key');
  }

  getInstance(): AxiosInstance {
    return this.client;
  }
}

export const apiClient = new ApiClient();
export type { ApiError };

