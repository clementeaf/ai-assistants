import { callFlowMCPTool } from './flows';

export interface Automaton {
  automaton_id: string;
  name: string;
  description: string | null;
  domain: string;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string | null;
  tags: string[];
  metadata: Record<string, unknown>;
}

export interface AutomatonVersion {
  version_id: string;
  automaton_id: string;
  version_number: number;
  system_prompt: string;
  prompt_hash: string | null;
  change_description: string | null;
  created_at: string;
  created_by: string | null;
  is_current: boolean;
}

export interface AutomatonTool {
  tool_id: string;
  automaton_id: string;
  tool_name: string;
  tool_description: string | null;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  is_required: boolean;
  created_at: string;
}

export interface AutomatonTest {
  test_id: string;
  automaton_id: string;
  test_name: string;
  test_description: string | null;
  test_type: 'unit' | 'integration' | 'e2e' | 'performance';
  scenario: Record<string, unknown>;
  expected_result: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface TestResult {
  result_id: string;
  test_id: string;
  automaton_id: string;
  version_id: string | null;
  execution_status: 'passed' | 'failed' | 'error' | 'skipped';
  actual_result: Record<string, unknown> | null;
  execution_time_ms: number | null;
  error_message: string | null;
  error_stack: string | null;
  executed_at: string;
  executed_by: string | null;
  metadata: Record<string, unknown>;
}

export interface AutomatonMetric {
  metric_id: string;
  automaton_id: string;
  version_id: string | null;
  metric_type: string;
  metric_value: number;
  metric_unit: string | null;
  evaluation_date: string;
  sample_size: number | null;
  metadata: Record<string, unknown>;
}

export interface AutomatonChange {
  change_id: string;
  automaton_id: string;
  change_type: string;
  change_description: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  changed_by: string | null;
  changed_at: string;
}

export interface AutomatonFullInfo extends Automaton {
  current_version: AutomatonVersion | null;
  versions: AutomatonVersion[];
  tools: AutomatonTool[];
  tests: AutomatonTest[];
  recent_test_results: TestResult[];
  metrics: AutomatonMetric[];
  recent_changes: AutomatonChange[];
}

export interface CreateAutomatonVersionRequest {
  automaton_id: string;
  system_prompt: string;
  change_description: string;
  created_by?: string;
}

export interface CreateAutomatonTestRequest {
  automaton_id: string;
  test_name: string;
  test_description?: string;
  test_type: 'unit' | 'integration' | 'e2e' | 'performance';
  test_scenario: Record<string, unknown>;
  expected_result?: Record<string, unknown>;
  created_by?: string;
}

/**
 * Obtiene información completa de un autómata
 */
export async function getAutomaton(automatonId: string): Promise<{ automaton: AutomatonFullInfo | null }> {
  return callFlowMCPTool<{ automaton: AutomatonFullInfo | null }>('get_automaton', { automaton_id: automatonId });
}

/**
 * Lista todos los autómatas
 */
export async function listAutomata(domain?: string, includeInactive = false): Promise<{ automata: Automaton[]; count: number }> {
  return callFlowMCPTool<{ automata: Automaton[]; count: number }>('list_automata', {
    domain,
    include_inactive: includeInactive,
  });
}

/**
 * Crea una nueva versión del prompt del autómata
 */
export async function createAutomatonVersion(request: CreateAutomatonVersionRequest): Promise<{
  version_id: string;
  version_number: number;
  automaton_id: string;
}> {
  return callFlowMCPTool('create_automaton_version', request);
}

/**
 * Crea un test para el autómata
 */
export async function createAutomatonTest(request: CreateAutomatonTestRequest): Promise<{
  test_id: string;
  test_name: string;
}> {
  return callFlowMCPTool('create_automaton_test', request);
}

/**
 * Obtiene resultados de tests de un autómata
 */
export async function getAutomatonTestResults(
  automatonId: string,
  testId?: string,
  limit = 50
): Promise<{ results: TestResult[]; count: number }> {
  return callFlowMCPTool<{ results: TestResult[]; count: number }>('get_automaton_test_results', {
    automaton_id: automatonId,
    test_id: testId,
    limit,
  });
}

/**
 * Obtiene métricas de un autómata
 */
export async function getAutomatonMetrics(
  automatonId: string,
  metricType?: string,
  limit = 50
): Promise<{ metrics: AutomatonMetric[]; count: number }> {
  return callFlowMCPTool<{ metrics: AutomatonMetric[]; count: number }>('get_automaton_metrics', {
    automaton_id: automatonId,
    metric_type: metricType,
    limit,
  });
}

/**
 * Obtiene el historial de cambios de un autómata
 */
export async function getAutomatonChanges(
  automatonId: string,
  limit = 50
): Promise<{ changes: AutomatonChange[]; count: number }> {
  return callFlowMCPTool<{ changes: AutomatonChange[]; count: number }>('get_automaton_changes', {
    automaton_id: automatonId,
    limit,
  });
}
