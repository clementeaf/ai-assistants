/**
 * API client for customer calendar management
 */

import { apiClient } from './client';

export interface CustomerCalendar {
  customer_id: string;
  customer_email: string;
  customer_name: string | null;
  calendar_connected: boolean;
  calendar_email: string | null;
  authorization_url: string | null;
  shareable_link: string | null;  // Link que se puede compartir con el cliente
}

export interface ConnectCustomerCalendarRequest {
  customer_id: string;
  customer_email: string;
  customer_name?: string | null;
}

export interface CustomerCalendarListResponse {
  customers: CustomerCalendar[];
}

/**
 * Conectar Google Calendar a un cliente
 */
export async function connectCustomerCalendar(
  request: ConnectCustomerCalendarRequest
): Promise<CustomerCalendar> {
  const response = await apiClient.getInstance().post<CustomerCalendar>(
    '/v1/customer-calendars/connect',
    request
  );
  return response.data;
}

/**
 * Obtener estado de conexión de calendario para un cliente
 */
export async function getCustomerCalendarStatus(
  customerId: string
): Promise<CustomerCalendar> {
  const response = await apiClient.getInstance().get<CustomerCalendar>(
    `/v1/customer-calendars/status/${customerId}`
  );
  return response.data;
}

/**
 * Listar todos los clientes con sus estados de calendario
 */
export async function listCustomerCalendars(): Promise<CustomerCalendarListResponse> {
  const response = await apiClient.getInstance().get<CustomerCalendarListResponse>(
    '/v1/customer-calendars/list'
  );
  return response.data;
}

/**
 * Desconectar Google Calendar de un cliente
 */
export async function disconnectCustomerCalendar(
  customerId: string
): Promise<{ message: string; customer_id: string }> {
  const response = await apiClient.getInstance().delete<{ message: string; customer_id: string }>(
    `/v1/customer-calendars/disconnect/${customerId}`
  );
  return response.data;
}
