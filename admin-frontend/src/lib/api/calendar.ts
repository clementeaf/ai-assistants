import axios from 'axios';

const CALENDAR_MCP_SERVER_URL = import.meta.env.VITE_CALENDAR_MCP_SERVER_URL || 'http://localhost:3000';

interface MCPRequest {
  jsonrpc: string;
  id: number | string;
  method: string;
  params: {
    name: string;
    arguments: Record<string, unknown>;
  };
}

interface MCPResponse<T = unknown> {
  jsonrpc: string;
  id: number | string;
  result?: T;
  error?: {
    code: number;
    message: string;
  };
}

/**
 * Llama a una herramienta del MCP server de calendario
 * @param toolName - Nombre de la herramienta a llamar
 * @param arguments_ - Argumentos para la herramienta
 * @returns Resultado de la llamada
 */
async function callCalendarMCPTool<T = unknown>(toolName: string, arguments_: Record<string, unknown>): Promise<T> {
  const payload: MCPRequest = {
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: arguments_,
    },
  };

  const response = await axios.post<MCPResponse<T>>(`${CALENDAR_MCP_SERVER_URL}/mcp`, payload);
  
  if (response.data.error) {
    throw new Error(response.data.error.message || 'Unknown MCP error');
  }

  if (!response.data.result) {
    throw new Error('No result in MCP response');
  }

  return response.data.result;
}

export interface Booking {
  booking_id: string;
  customer_id: string;
  customer_name: string;
  date_iso: string;
  start_time_iso: string;
  end_time_iso: string;
  status: string;
  created_at: string;
  confirmation_email_sent: boolean;
  reminder_sent: boolean;
}

export interface BookingSlot {
  date_iso: string;
  start_time_iso: string;
  end_time_iso: string;
  available: boolean;
}

export interface CheckAvailabilityRequest {
  date_iso: string;
  start_time_iso: string;
  end_time_iso: string;
}

export interface CheckAvailabilityResponse {
  available: boolean;
}

export interface GetAvailableSlotsRequest {
  date_iso: string;
}

export interface GetAvailableSlotsResponse {
  slots: BookingSlot[];
}

export interface CreateBookingRequest {
  customer_id: string;
  customer_name: string;
  date_iso: string;
  start_time_iso: string;
  end_time_iso: string;
}

export interface CreateBookingResponse {
  booking: Booking;
}

export interface GetBookingRequest {
  booking_id: string;
}

export interface GetBookingResponse {
  booking: Booking | null;
}

export interface ListBookingsRequest {
  customer_id: string;
}

export interface ListBookingsResponse {
  bookings: Booking[];
}

export interface UpdateBookingRequest {
  booking_id: string;
  date_iso?: string;
  start_time_iso?: string;
  end_time_iso?: string;
  status?: string;
}

export interface UpdateBookingResponse {
  booking: Booking;
}

export interface DeleteBookingRequest {
  booking_id: string;
}

export interface DeleteBookingResponse {
  success: boolean;
}

/**
 * Verifica si un horario está disponible
 */
export async function checkAvailability(request: CheckAvailabilityRequest): Promise<CheckAvailabilityResponse> {
  return callCalendarMCPTool<CheckAvailabilityResponse>('check_availability', request);
}

/**
 * Obtiene los horarios disponibles para una fecha
 */
export async function getAvailableSlots(request: GetAvailableSlotsRequest): Promise<GetAvailableSlotsResponse> {
  return callCalendarMCPTool<GetAvailableSlotsResponse>('get_available_slots', request);
}

/**
 * Crea una nueva reserva
 */
export async function createBooking(request: CreateBookingRequest): Promise<CreateBookingResponse> {
  return callCalendarMCPTool<CreateBookingResponse>('create_booking', request);
}

/**
 * Obtiene una reserva por ID
 */
export async function getBooking(request: GetBookingRequest): Promise<GetBookingResponse> {
  return callCalendarMCPTool<GetBookingResponse>('get_booking', request);
}

/**
 * Lista las reservas de un cliente
 */
export async function listBookings(request: ListBookingsRequest): Promise<ListBookingsResponse> {
  return callCalendarMCPTool<ListBookingsResponse>('list_bookings', request);
}

/**
 * Actualiza una reserva
 */
export async function updateBooking(request: UpdateBookingRequest): Promise<UpdateBookingResponse> {
  return callCalendarMCPTool<UpdateBookingResponse>('update_booking', request);
}

/**
 * Elimina una reserva
 */
export async function deleteBooking(request: DeleteBookingRequest): Promise<DeleteBookingResponse> {
  return callCalendarMCPTool<DeleteBookingResponse>('delete_booking', request);
}
