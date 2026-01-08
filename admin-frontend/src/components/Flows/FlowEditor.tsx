import { useState, useRef, useEffect } from 'react';
import type { FlowStage } from '../../lib/api/flows';

interface FlowEditorProps {
  stages: FlowStage[];
  onStageSelect?: (stage: FlowStage | null) => void;
  onStageMove?: (stageId: string, x: number, y: number) => void;
}

/**
 * Editor visual de flujo de conversación
 * Permite visualizar y editar la estructura de diálogo
 * @param stages - Etapas del flujo
 * @param onStageSelect - Callback cuando se selecciona una etapa
 * @param onStageMove - Callback cuando se mueve una etapa
 * @returns Componente FlowEditor renderizado
 */
function FlowEditor({ stages, onStageSelect, onStageMove }: FlowEditorProps) {
  const [selectedStageId, setSelectedStageId] = useState<string | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [stagePositions, setStagePositions] = useState<Record<string, { x: number; y: number }>>({});
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const initialPositions: Record<string, { x: number; y: number }> = {};
    stages.forEach((stage, index) => {
      if (!stagePositions[stage.stage_id]) {
        initialPositions[stage.stage_id] = {
          x: 100,
          y: 100 + index * 150,
        };
      }
    });
    if (Object.keys(initialPositions).length > 0) {
      setStagePositions((prev) => ({ ...prev, ...initialPositions }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stages]);

  const handleStageClick = (stage: FlowStage): void => {
    setSelectedStageId(stage.stage_id);
    onStageSelect?.(stage);
  };

  const handleStageMouseDown = (e: React.MouseEvent, stageId: string): void => {
    e.stopPropagation();
    setDragging(stageId);
    const stagePos = stagePositions[stageId] || { x: 100, y: 100 };
    setDragOffset({
      x: e.clientX - stagePos.x,
      y: e.clientY - stagePos.y,
    });
  };

  const handleMouseMove = (e: MouseEvent): void => {
    if (!dragging || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - containerRect.left - dragOffset.x;
    const y = e.clientY - containerRect.top - dragOffset.y;

    setStagePositions((prev) => ({
      ...prev,
      [dragging]: { x: Math.max(0, x), y: Math.max(0, y) },
    }));
  };

  const handleMouseUp = (): void => {
    if (dragging && onStageMove) {
      const pos = stagePositions[dragging];
      if (pos) {
        onStageMove(dragging, pos.x, pos.y);
      }
    }
    setDragging(null);
  };

  useEffect(() => {
    if (dragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dragging, dragOffset, stagePositions, onStageMove]);

  const handleContainerClick = (): void => {
    setSelectedStageId(null);
    onStageSelect?.(null);
  };

  const getStageTypeColor = (type: string): string => {
    switch (type) {
      case 'greeting':
        return 'bg-green-500';
      case 'input':
        return 'bg-blue-500';
      case 'confirmation':
        return 'bg-yellow-500';
      case 'action':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const sortedStages = [...stages].sort((a, b) => a.stage_order - b.stage_order);

  return (
    <div
      ref={containerRef}
      className="w-full h-full bg-gray-50 border-2 border-gray-300 rounded-lg relative overflow-hidden cursor-default"
      onClick={handleContainerClick}
    >
      <svg
        className="absolute pointer-events-none"
        style={{
          left: 0,
          top: 0,
          width: '100%',
          height: '100%',
          zIndex: 0,
        }}
      >
        {sortedStages.map((stage, index) => {
          if (index === 0) return null;
          const prevPos = stagePositions[sortedStages[index - 1].stage_id] || {
            x: 100,
            y: 100 + (index - 1) * 150,
          };
          const currentPos = stagePositions[stage.stage_id] || {
            x: 100,
            y: 100 + index * 150,
          };
          return (
            <line
              key={`line-${stage.stage_id}`}
              x1={prevPos.x + 100}
              y1={prevPos.y + 60}
              x2={currentPos.x + 100}
              y2={currentPos.y + 20}
              stroke="#9ca3af"
              strokeWidth="2"
              markerEnd="url(#arrowhead)"
            />
          );
        })}
      </svg>

      {sortedStages.map((stage, index) => {
        const pos = stagePositions[stage.stage_id] || { x: 100, y: 100 + index * 150 };
        const isSelected = selectedStageId === stage.stage_id;
        const isDragging = dragging === stage.stage_id;

        return (
          <div key={stage.stage_id}>
            <div
              className={`absolute cursor-move rounded-lg shadow-lg border-2 transition-all ${
                isSelected ? 'border-blue-600 ring-2 ring-blue-300' : 'border-gray-400'
              } ${isDragging ? 'opacity-75' : ''}`}
              style={{
                left: `${pos.x}px`,
                top: `${pos.y}px`,
                width: '200px',
                zIndex: isDragging ? 10 : 1,
              }}
              onClick={(e) => {
                e.stopPropagation();
                handleStageClick(stage);
              }}
              onMouseDown={(e) => handleStageMouseDown(e, stage.stage_id)}
            >
              <div className={`${getStageTypeColor(stage.stage_type)} text-white px-3 py-2 rounded-t-lg`}>
                <div className="font-semibold text-sm">{stage.stage_name}</div>
                <div className="text-xs opacity-90">{stage.stage_type}</div>
              </div>
              <div className="bg-white px-3 py-2 rounded-b-lg">
                <div className="text-xs text-gray-600 line-clamp-2">
                  {stage.prompt_text || 'Sin prompt'}
                </div>
                {stage.field_name && (
                  <div className="text-xs text-gray-500 mt-1">
                    {stage.field_name} {stage.is_required && <span className="text-red-500">*</span>}
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}

      <svg className="absolute pointer-events-none" style={{ width: 0, height: 0 }}>
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#9ca3af" />
          </marker>
        </defs>
      </svg>

      {stages.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <div className="text-lg mb-2">No hay etapas en este flujo</div>
            <div className="text-sm">Agrega etapas para visualizar la estructura del diálogo</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default FlowEditor;
