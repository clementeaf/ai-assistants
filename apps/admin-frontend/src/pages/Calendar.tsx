import { useState, useEffect } from 'react';
import {
  checkAvailability,
  getAvailableSlots,
  createBooking,
  getBooking,
  listBookings,
  updateBooking,
  deleteBooking,
  type Booking,
  type BookingSlot,
  type CreateBookingRequest,
  type UpdateBookingRequest,
} from '../lib/api/calendar';
import { format, parseISO, startOfWeek, addDays, isSameDay, isToday } from 'date-fns';

/**
 * Página para gestionar el calendario y reservas
 * @returns Componente de calendario renderizado
 */
function Calendar() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [availableSlots, setAvailableSlots] = useState<BookingSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateBooking, setShowCreateBooking] = useState(false);
  const [showBookingDetails, setShowBookingDetails] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  const [customerId, setCustomerId] = useState('');
  const [customerName, setCustomerName] = useState('');

  const weekStart = startOfWeek(selectedDate, { weekStartsOn: 1 });
  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const loadAvailableSlots = async (date: Date): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const dateIso = format(date, 'yyyy-MM-dd');
      const response = await getAvailableSlots({ date_iso: dateIso });
      setAvailableSlots(response.slots);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar horarios disponibles');
    } finally {
      setLoading(false);
    }
  };

  const loadBookings = async (): Promise<void> => {
    if (!customerId.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await listBookings({ customer_id: customerId });
      setBookings(response.bookings);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar reservas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAvailableSlots(selectedDate);
  }, [selectedDate]);

  const getBookingsForDate = (date: Date): Booking[] => {
    const dateIso = format(date, 'yyyy-MM-dd');
    return bookings.filter((booking) => booking.date_iso === dateIso);
  };

  const handleCreateBooking = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const dateIso = formData.get('date') as string;
    const startTime = formData.get('start_time') as string;
    const endTime = formData.get('end_time') as string;
    const customerIdValue = formData.get('customer_id') as string;
    const customerNameValue = formData.get('customer_name') as string;

    const request: CreateBookingRequest = {
      customer_id: customerIdValue,
      customer_name: customerNameValue,
      date_iso: dateIso,
      start_time_iso: `${dateIso}T${startTime}:00Z`,
      end_time_iso: `${dateIso}T${endTime}:00Z`,
    };

    setLoading(true);
    setError(null);
    try {
      await createBooking(request);
      setShowCreateBooking(false);
      await loadAvailableSlots(parseISO(dateIso));
      if (customerIdValue === customerId) {
        await loadBookings();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al crear reserva');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateBooking = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!selectedBooking) return;

    const formData = new FormData(e.currentTarget);
    const dateIso = formData.get('date') as string;
    const startTime = formData.get('start_time') as string;
    const endTime = formData.get('end_time') as string;
    const status = formData.get('status') as string;

    const request: UpdateBookingRequest = {
      booking_id: selectedBooking.booking_id,
      date_iso: dateIso,
      start_time_iso: startTime ? `${dateIso}T${startTime}:00Z` : undefined,
      end_time_iso: endTime ? `${dateIso}T${endTime}:00Z` : undefined,
      status: status || undefined,
    };

    setLoading(true);
    setError(null);
    try {
      await updateBooking(request);
      setShowBookingDetails(false);
      setSelectedBooking(null);
      await loadAvailableSlots(selectedDate);
      if (customerId) {
        await loadBookings();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar reserva');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBooking = async (bookingId: string): Promise<void> => {
    if (!confirm('¿Estás seguro de eliminar esta reserva?')) return;

    setLoading(true);
    setError(null);
    try {
      await deleteBooking({ booking_id: bookingId });
      setShowBookingDetails(false);
      setSelectedBooking(null);
      await loadAvailableSlots(selectedDate);
      if (customerId) {
        await loadBookings();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al eliminar reserva');
    } finally {
      setLoading(false);
    }
  };

  const handleDateClick = (date: Date): void => {
    setSelectedDate(date);
    setShowCreateBooking(true);
  };

  const handleBookingClick = async (bookingId: string): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const response = await getBooking({ booking_id: bookingId });
      if (response.booking) {
        setSelectedBooking(response.booking);
        setShowBookingDetails(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar reserva');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Calendario de Reservas</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setSelectedDate(new Date())}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            Hoy
          </button>
          <button
            onClick={() => setSelectedDate(addDays(selectedDate, -7))}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            Semana Anterior
          </button>
          <button
            onClick={() => setSelectedDate(addDays(selectedDate, 7))}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            Semana Siguiente
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">Buscar Reservas por Cliente</h2>
        <div className="flex gap-2">
          <input
            type="text"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            placeholder="ID del Cliente"
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <input
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            placeholder="Nombre del Cliente"
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <button
            onClick={loadBookings}
            disabled={!customerId.trim() || loading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
          >
            Buscar
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-100 border border-red-300 text-red-800 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-7 gap-2">
        {weekDays.map((day) => {
          const dayBookings = getBookingsForDate(day);
          const isSelected = isSameDay(day, selectedDate);
          const isTodayDate = isToday(day);

          return (
            <div
              key={day.toISOString()}
              className={`border rounded-lg p-2 min-h-32 cursor-pointer transition-colors ${
                isSelected
                  ? 'bg-blue-100 border-blue-500'
                  : isTodayDate
                    ? 'bg-yellow-50 border-yellow-300'
                    : 'bg-white border-gray-300 hover:bg-gray-50'
              }`}
              onClick={() => handleDateClick(day)}
            >
              <div className="text-sm font-semibold mb-2">
                {format(day, 'EEE')}
              </div>
              <div className={`text-lg font-bold mb-2 ${isTodayDate ? 'text-blue-600' : ''}`}>
                {format(day, 'd')}
              </div>
              <div className="space-y-1">
                {dayBookings.slice(0, 3).map((booking) => (
                  <div
                    key={booking.booking_id}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleBookingClick(booking.booking_id);
                    }}
                    className="text-xs bg-blue-500 text-white p-1 rounded truncate cursor-pointer hover:bg-blue-600"
                    title={`${booking.customer_name} - ${format(parseISO(booking.start_time_iso), 'HH:mm')}`}
                  >
                    {format(parseISO(booking.start_time_iso), 'HH:mm')} - {booking.customer_name}
                  </div>
                ))}
                {dayBookings.length > 3 && (
                  <div className="text-xs text-gray-500">
                    +{dayBookings.length - 3} más
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {selectedDate && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">
            Horarios Disponibles - {format(selectedDate, 'EEEE, d MMMM yyyy')}
          </h2>
          {loading ? (
            <div className="text-gray-500">Cargando...</div>
          ) : availableSlots.length === 0 ? (
            <div className="text-gray-500">No hay horarios disponibles</div>
          ) : (
            <div className="grid grid-cols-4 gap-2">
              {availableSlots.map((slot, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border text-center ${
                    slot.available
                      ? 'bg-green-50 border-green-300 text-green-800'
                      : 'bg-red-50 border-red-300 text-red-800'
                  }`}
                >
                  <div className="font-semibold">
                    {format(parseISO(slot.start_time_iso), 'HH:mm')} -{' '}
                    {format(parseISO(slot.end_time_iso), 'HH:mm')}
                  </div>
                  <div className="text-xs mt-1">
                    {slot.available ? 'Disponible' : 'Ocupado'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {showCreateBooking && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h2 className="text-xl font-semibold mb-4">Crear Nueva Reserva</h2>
            <form onSubmit={handleCreateBooking}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Fecha</label>
                  <input
                    type="date"
                    name="date"
                    defaultValue={format(selectedDate, 'yyyy-MM-dd')}
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Hora Inicio (HH:MM)</label>
                  <input
                    type="time"
                    name="start_time"
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Hora Fin (HH:MM)</label>
                  <input
                    type="time"
                    name="end_time"
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">ID del Cliente</label>
                  <input
                    type="text"
                    name="customer_id"
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Nombre del Cliente</label>
                  <input
                    type="text"
                    name="customer_name"
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
                >
                  Crear
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateBooking(false)}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showBookingDetails && selectedBooking && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h2 className="text-xl font-semibold mb-4">Detalles de la Reserva</h2>
            <form onSubmit={handleUpdateBooking}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">ID de Reserva</label>
                  <input
                    type="text"
                    value={selectedBooking.booking_id}
                    disabled
                    className="w-full px-3 py-2 border rounded-lg bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Cliente</label>
                  <input
                    type="text"
                    value={selectedBooking.customer_name}
                    disabled
                    className="w-full px-3 py-2 border rounded-lg bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Fecha</label>
                  <input
                    type="date"
                    name="date"
                    defaultValue={selectedBooking.date_iso}
                    required
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Hora Inicio (HH:MM)</label>
                  <input
                    type="time"
                    name="start_time"
                    defaultValue={format(parseISO(selectedBooking.start_time_iso), 'HH:mm')}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Hora Fin (HH:MM)</label>
                  <input
                    type="time"
                    name="end_time"
                    defaultValue={format(parseISO(selectedBooking.end_time_iso), 'HH:mm')}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Estado</label>
                  <select
                    name="status"
                    defaultValue={selectedBooking.status}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="pending">Pendiente</option>
                    <option value="confirmed">Confirmado</option>
                    <option value="cancelled">Cancelado</option>
                    <option value="completed">Completado</option>
                  </select>
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
                >
                  Actualizar
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteBooking(selectedBooking.booking_id)}
                  disabled={loading}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-gray-300 transition-colors"
                >
                  Eliminar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowBookingDetails(false);
                    setSelectedBooking(null);
                  }}
                  className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  Cerrar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Calendar;
