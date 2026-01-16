-- Esquema de base de datos para gestión completa de autómatas
-- Incluye: versionado, tests, métricas, cambios, herramientas

-- Tabla principal de autómatas (expandida)
CREATE TABLE IF NOT EXISTS automata (
    automaton_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    domain TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT,
    tags TEXT, -- JSON array de tags
    metadata_json TEXT -- JSON con metadatos adicionales
);

-- Versiones de prompts del autómata (versionado)
CREATE TABLE IF NOT EXISTS automata_versions (
    version_id TEXT PRIMARY KEY,
    automaton_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    system_prompt TEXT NOT NULL,
    prompt_hash TEXT, -- Hash del prompt para detectar cambios
    change_description TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT,
    is_current INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
    UNIQUE(automaton_id, version_number)
);

-- Herramientas/funciones usadas por cada autómata
CREATE TABLE IF NOT EXISTS automata_tools (
    tool_id TEXT PRIMARY KEY,
    automaton_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    tool_description TEXT,
    tool_input_schema TEXT, -- JSON schema
    tool_output_schema TEXT, -- JSON schema
    is_required INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
    UNIQUE(automaton_id, tool_name)
);

-- Tests definidos para autómatas
CREATE TABLE IF NOT EXISTS automata_tests (
    test_id TEXT PRIMARY KEY,
    automaton_id TEXT NOT NULL,
    test_name TEXT NOT NULL,
    test_description TEXT,
    test_type TEXT NOT NULL, -- 'unit', 'integration', 'e2e', 'performance'
    test_scenario TEXT NOT NULL, -- JSON con el escenario de prueba
    expected_result TEXT, -- JSON con resultado esperado
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_by TEXT,
    FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE
);

-- Resultados de ejecución de tests
CREATE TABLE IF NOT EXISTS automata_test_results (
    result_id TEXT PRIMARY KEY,
    test_id TEXT NOT NULL,
    automaton_id TEXT NOT NULL,
    version_id TEXT, -- Versión del autómata probada
    execution_status TEXT NOT NULL, -- 'passed', 'failed', 'error', 'skipped'
    actual_result TEXT, -- JSON con resultado real
    execution_time_ms INTEGER,
    error_message TEXT,
    error_stack TEXT,
    executed_at TEXT NOT NULL,
    executed_by TEXT,
    metadata_json TEXT, -- JSON con métricas adicionales
    FOREIGN KEY (test_id) REFERENCES automata_tests(test_id) ON DELETE CASCADE,
    FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES automata_versions(version_id) ON DELETE SET NULL
);

-- Historial de cambios en autómatas
CREATE TABLE IF NOT EXISTS automata_changes (
    change_id TEXT PRIMARY KEY,
    automaton_id TEXT NOT NULL,
    change_type TEXT NOT NULL, -- 'prompt_update', 'stage_add', 'stage_remove', 'stage_modify', 'tool_add', 'tool_remove', 'test_add', 'test_remove'
    change_description TEXT NOT NULL,
    before_state TEXT, -- JSON con estado anterior
    after_state TEXT, -- JSON con estado nuevo
    changed_by TEXT,
    changed_at TEXT NOT NULL,
    FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE
);

-- Métricas de rendimiento y evaluación
CREATE TABLE IF NOT EXISTS automata_metrics (
    metric_id TEXT PRIMARY KEY,
    automaton_id TEXT NOT NULL,
    version_id TEXT, -- Versión específica evaluada
    metric_type TEXT NOT NULL, -- 'accuracy', 'response_time', 'user_satisfaction', 'error_rate', 'success_rate'
    metric_value REAL NOT NULL,
    metric_unit TEXT, -- 'percentage', 'milliseconds', 'count', etc.
    evaluation_date TEXT NOT NULL,
    sample_size INTEGER,
    metadata_json TEXT, -- JSON con contexto adicional
    FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES automata_versions(version_id) ON DELETE SET NULL
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_automata_domain ON automata(domain);
CREATE INDEX IF NOT EXISTS idx_automata_active ON automata(is_active);
CREATE INDEX IF NOT EXISTS idx_automata_versions_automaton ON automata_versions(automaton_id);
CREATE INDEX IF NOT EXISTS idx_automata_versions_current ON automata_versions(automaton_id, is_current);
CREATE INDEX IF NOT EXISTS idx_automata_tools_automaton ON automata_tools(automaton_id);
CREATE INDEX IF NOT EXISTS idx_automata_tests_automaton ON automata_tests(automaton_id);
CREATE INDEX IF NOT EXISTS idx_automata_tests_active ON automata_tests(automaton_id, is_active);
CREATE INDEX IF NOT EXISTS idx_test_results_test ON automata_test_results(test_id);
CREATE INDEX IF NOT EXISTS idx_test_results_automaton ON automata_test_results(automaton_id);
CREATE INDEX IF NOT EXISTS idx_test_results_status ON automata_test_results(execution_status);
CREATE INDEX IF NOT EXISTS idx_test_results_executed ON automata_test_results(executed_at);
CREATE INDEX IF NOT EXISTS idx_changes_automaton ON automata_changes(automaton_id);
CREATE INDEX IF NOT EXISTS idx_changes_date ON automata_changes(changed_at);
CREATE INDEX IF NOT EXISTS idx_metrics_automaton ON automata_metrics(automaton_id);
CREATE INDEX IF NOT EXISTS idx_metrics_type ON automata_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON automata_metrics(evaluation_date);
