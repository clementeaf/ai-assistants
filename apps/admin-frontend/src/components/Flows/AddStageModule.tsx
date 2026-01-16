interface AddStageModuleProps {
  onAddModule: (moduleType: string) => void;
  onClose?: () => void;
}

/**
 * Componente para agregar módulos preformulados
 * @param onAddModule - Callback cuando se selecciona un tipo de módulo
 * @returns Componente AddStageModule renderizado
 */
function AddStageModule({ onAddModule, onClose }: AddStageModuleProps) {
  const moduleTypes = [
    {
      id: 'greeting',
      label: 'Saludo',
      description: 'Mensaje de bienvenida inicial (el sistema obtiene el nombre automáticamente)',
    },
    {
      id: 'input_date',
      label: 'Solicitar Fecha',
      description: 'El asistente pedirá una fecha (formato preconfigurado)',
    },
    {
      id: 'input_time',
      label: 'Solicitar Hora',
      description: 'El asistente pedirá una hora (formato preconfigurado)',
    },
    {
      id: 'input_text',
      label: 'Solicitar Texto',
      description: 'El asistente pedirá información en texto',
    },
    {
      id: 'input_name',
      label: 'Solicitar Nombre',
      description: 'Solo se activa si el sistema no encontró el nombre de WhatsApp',
    },
    {
      id: 'input_email',
      label: 'Solicitar Email',
      description: 'El asistente pedirá un email (formato preconfigurado)',
    },
    {
      id: 'input_number',
      label: 'Solicitar Número',
      description: 'El asistente pedirá un número (formato preconfigurado)',
    },
    {
      id: 'confirmation',
      label: 'Confirmación',
      description: 'El asistente pedirá confirmar antes de continuar',
    },
    {
      id: 'system_prompt',
      label: 'Prompt del Sistema LLM',
      description: 'Prompt completo del LLM que conecta con Google Calendar (solo para flujos de bookings)',
    },
  ];

  return (
    <div className="bg-white rounded-lg border-2 border-blue-300 p-4 shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <div>
          <div className="text-lg font-semibold text-gray-700 mb-1">Agregar Módulo Preformulado</div>
          <div className="text-sm text-gray-500">Selecciona el tipo de módulo que quieres agregar</div>
        </div>
        <button
          onClick={() => {
            if (onClose) {
              onClose();
            } else {
              onAddModule('');
            }
          }}
          className="text-gray-500 hover:text-gray-700 text-xl font-bold"
          title="Cerrar"
        >
          X
        </button>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {moduleTypes.map((module) => (
          <button
            key={module.id}
            onClick={() => onAddModule(module.id)}
            className="p-3 text-left border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
          >
            <div className="mb-1">
              <span className="font-semibold text-sm">{module.label}</span>
            </div>
            <div className="text-xs text-gray-600">{module.description}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

export default AddStageModule;
