#!/bin/bash
# Script para iniciar todos los servidores MCP

set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/tmp"

echo "🚀 Iniciando servidores MCP..."
echo ""

# Función para iniciar un servidor
start_server() {
    local server_name=$1
    local server_dir=$2
    local port=$3
    
    echo "📦 Iniciando $server_name en puerto $port..."
    cd "$BASE_DIR/$server_dir"
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        python main.py > "$LOG_DIR/${server_name}-mcp.log" 2>&1 &
        echo "   ✓ $server_name iniciado (PID: $!)"
    else
        echo "   ✗ Error: No se encontró .venv en $server_dir"
        return 1
    fi
    
    sleep 1
}

# Iniciar todos los servidores
start_server "calendar" "calendar-mcp-server" "60000"
start_server "professionals" "professionals-mcp-server" "60002"
start_server "booking-log" "booking-log-mcp-server" "60003"
start_server "llm" "llm-mcp-server" "60004"
start_server "booking-flow" "booking-flow-mcp-server" "60006"

echo ""
echo "⏳ Esperando que los servidores inicien..."
sleep 3

echo ""
echo "🔍 Verificando servidores..."
echo ""

# Verificar cada servidor
check_server() {
    local name=$1
    local port=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "   ✓ $name (:$port) - OK"
        return 0
    else
        echo "   ✗ $name (:$port) - ERROR"
        return 1
    fi
}

check_server "Calendar" "60000"
check_server "Professionals" "60002"
check_server "Booking Log" "60003"
check_server "LLM" "60004"
check_server "Booking Flow" "60006"

echo ""
echo "✅ Todos los servidores MCP están corriendo"
echo ""
echo "📋 Logs disponibles en:"
echo "   - Calendar: $LOG_DIR/calendar-mcp.log"
echo "   - Professionals: $LOG_DIR/professionals-mcp.log"
echo "   - Booking Log: $LOG_DIR/booking-log-mcp.log"
echo "   - LLM: $LOG_DIR/llm-mcp.log"
echo "   - Booking Flow: $LOG_DIR/booking-flow-mcp.log"
echo ""
echo "🛑 Para detener los servidores, ejecuta:"
echo "   pkill -f 'python.*main.py'"
