import axios from 'axios';

const FLOW_MCP_SERVER_URL = import.meta.env.VITE_FLOW_MCP_SERVER_URL || 'http://localhost:60006';

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
 * Llama a una herramienta del MCP server de flujos
 * @param toolName - Nombre de la herramienta a llamar
 * @param arguments_ - Argumentos para la herramienta
 * @returns Resultado de la llamada
 */
async function callFlowMCPTool<T = unknown>(toolName: string, arguments_: Record<string, unknown>): Promise<T> {
  const payload: MCPRequest = {
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: arguments_,
    },
  };

  try {
    const response = await axios.post<MCPResponse<T>>(`${FLOW_MCP_SERVER_URL}/mcp`, payload);
    
    if (response.data.error) {
      const errorMsg = response.data.error.message || 'Unknown MCP error';
      console.error(`MCP Error for tool "${toolName}":`, errorMsg);
      throw new Error(`MCP Error: ${errorMsg}`);
    }

    if (!response.data.result) {
      throw new Error('No result in MCP response');
    }

    return response.data.result;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        throw new Error(
          `No se pudo conectar al servidor MCP de flujos en ${FLOW_MCP_SERVER_URL}. ` +
          `Verifica que el servidor esté corriendo en el puerto 60006 (o el configurado en VITE_FLOW_MCP_SERVER_URL)`
        );
      }
      if (error.response) {
        const status = error.response.status;
        const errorData = error.response.data;
        throw new Error(
          `Error del servidor MCP (${status}): ${errorData?.error?.message || error.message}`
        );
      }
    }
    throw error;
  }
}

export interface Flow {
  flow_id: string;
  name: string;
  description: string | null;
  domain: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FlowStage {
  stage_id: string;
  flow_id: string;
  stage_order: number;
  stage_name: string;
  stage_type: string;
  prompt_text: string | null;
  field_name: string | null;
  field_type: string | null;
  validation_rules: string | null;
  is_required: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateFlowRequest {
  name: string;
  description?: string;
  domain?: string;
}

export interface CreateFlowResponse {
  flow: Flow;
}

export interface GetFlowResponse {
  flow: Flow | null;
}

export interface ListFlowsResponse {
  flows: Flow[];
  count: number;
}

export interface AddStageRequest {
  flow_id: string;
  stage_order: number;
  stage_name: string;
  stage_type: string;
  prompt_text?: string;
  field_name?: string;
  field_type?: string;
  validation_rules?: string;
  is_required?: boolean;
}

export interface AddStageResponse {
  stage: FlowStage;
}

export interface GetFlowStagesResponse {
  stages: FlowStage[];
  count: number;
}

export interface UpdateStageRequest {
  stage_id: string;
  stage_order?: number;
  stage_name?: string;
  prompt_text?: string;
  field_name?: string;
  field_type?: string;
  validation_rules?: string;
  is_required?: boolean;
}

export interface UpdateStageResponse {
  stage: FlowStage;
}

export interface DeleteStageResponse {
  success: boolean;
}

export interface DeleteFlowResponse {
  success: boolean;
}

/**
 * Crea un nuevo flujo de conversación
 */
export async function createFlow(request: CreateFlowRequest): Promise<CreateFlowResponse> {
  return callFlowMCPTool<CreateFlowResponse>('create_flow', request);
}

/**
 * Obtiene un flujo por ID o dominio
 */
export async function getFlow(flowId?: string, domain?: string): Promise<GetFlowResponse> {
  const args: Record<string, unknown> = {};
  if (flowId) args.flow_id = flowId;
  if (domain) args.domain = domain;
  return callFlowMCPTool<GetFlowResponse>('get_flow', args);
}

/**
 * Lista todos los flujos
 */
export async function listFlows(domain?: string, includeInactive = false): Promise<ListFlowsResponse> {
  const args: Record<string, unknown> = { include_inactive: includeInactive };
  if (domain) args.domain = domain;
  return callFlowMCPTool<ListFlowsResponse>('list_flows', args);
}

/**
 * Agrega una etapa a un flujo
 */
export async function addStage(request: AddStageRequest): Promise<AddStageResponse> {
  return callFlowMCPTool<AddStageResponse>('add_stage', request);
}

/**
 * Obtiene todas las etapas de un flujo
 */
export async function getFlowStages(flowId: string): Promise<GetFlowStagesResponse> {
  return callFlowMCPTool<GetFlowStagesResponse>('get_flow_stages', { flow_id: flowId });
}

/**
 * Actualiza una etapa
 */
export async function updateStage(request: UpdateStageRequest): Promise<UpdateStageResponse> {
  return callFlowMCPTool<UpdateStageResponse>('update_stage', request);
}

/**
 * Elimina una etapa
 */
export async function deleteStage(stageId: string): Promise<DeleteStageResponse> {
  return callFlowMCPTool<DeleteStageResponse>('delete_stage', { stage_id: stageId });
}

/**
 * Elimina un flujo y todas sus etapas
 */
export async function deleteFlow(flowId: string): Promise<DeleteFlowResponse> {
  return callFlowMCPTool<DeleteFlowResponse>('delete_flow', { flow_id: flowId });
}
