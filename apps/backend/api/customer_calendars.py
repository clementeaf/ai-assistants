"""API endpoints for managing customer Google Calendar connections."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr

from ai_assistants.security.auth import AuthContext, require_auth
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, load_sqlite_memory_store_config
from ai_assistants.config.mcp_config import load_mcp_config

router = APIRouter(prefix="/v1/customer-calendars", tags=["customer-calendars"])

# Store instance (will be initialized in app.py)
_memory_store: SqliteCustomerMemoryStore | None = None


def set_memory_store(store: SqliteCustomerMemoryStore) -> None:
    """Set the memory store instance."""
    global _memory_store
    _memory_store = store


def _get_calendar_mcp_url() -> str | None:
    """Get the calendar MCP server URL."""
    mcp_config = load_mcp_config()
    if mcp_config.calendar is None:
        return None
    return mcp_config.calendar.server_url.rstrip("/")


class CustomerCalendarRequest(BaseModel):
    """Request to connect a customer email to Google Calendar."""

    customer_id: str
    customer_email: EmailStr
    customer_name: str | None = None


class CustomerCalendarResponse(BaseModel):
    """Response with customer calendar connection info."""

    customer_id: str
    customer_email: str
    customer_name: str | None
    calendar_connected: bool
    calendar_email: str | None = None
    authorization_url: str | None = None
    shareable_link: str | None = None  # Link que se puede compartir con el cliente


class CustomerCalendarListResponse(BaseModel):
    """Response with list of customer calendar connections."""

    customers: list[CustomerCalendarResponse]


@router.post("/connect", response_model=CustomerCalendarResponse)
async def connect_customer_calendar(
    request: CustomerCalendarRequest,
    auth: AuthContext = Depends(require_auth),
) -> CustomerCalendarResponse:
    """
    Iniciar conexión de Google Calendar para un cliente.
    
    Genera URL de autorización OAuth2 que el admin debe abrir para conectar el calendario.
    
    Flujo:
    1. Admin ingresa email del cliente en admin-frontend
    2. Este endpoint genera URL de autorización OAuth2
    3. Admin (o cliente) abre la URL y autoriza acceso
    4. Google redirige al callback del MCP Calendar Server
    5. Los tokens se guardan encriptados
    6. El asistente IA puede usar el calendario del cliente automáticamente
    """
    if _memory_store is None:
        raise HTTPException(status_code=500, detail="Memory store not configured")
    
    # Almacenar email del cliente en customer_memory
    memory = _memory_store.get(project_id=auth.project_id, customer_id=request.customer_id)
    memory_data = memory.data if memory else {}
    
    # Guardar email del cliente
    memory_data["customer_email"] = request.customer_email
    if request.customer_name:
        memory_data["customer_name"] = request.customer_name
    
    _memory_store.upsert(project_id=auth.project_id, customer_id=request.customer_id, data=memory_data)
    
    # Obtener URL de autorización del MCP Calendar Server
    mcp_url = _get_calendar_mcp_url()
    authorization_url = None
    shareable_link = None
    
    if mcp_url:
        try:
            # Llamar al endpoint de OAuth2 del MCP Calendar Server
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{mcp_url}/oauth/authorize",
                    json={"customer_id": request.customer_id},
                )
                response.raise_for_status()
                data = response.json()
                authorization_url = data.get("authorization_url")
                
                # Crear link compartible que el admin puede enviar al cliente
                # Este link se puede compartir por WhatsApp, email, etc.
                if authorization_url:
                    shareable_link = authorization_url
        except Exception as e:
            # Si falla, continuar sin URL (el admin puede configurar manualmente)
            pass
    
    return CustomerCalendarResponse(
        customer_id=request.customer_id,
        customer_email=request.customer_email,
        customer_name=request.customer_name,
        calendar_connected=False,
        authorization_url=authorization_url,
        shareable_link=shareable_link,
    )


@router.get("/status/{customer_id}", response_model=CustomerCalendarResponse)
async def get_customer_calendar_status(
    customer_id: str,
    auth: AuthContext = Depends(require_auth),
) -> CustomerCalendarResponse:
    """Obtener estado de conexión de Google Calendar para un cliente."""
    if _memory_store is None:
        raise HTTPException(status_code=500, detail="Memory store not configured")
    
    memory = _memory_store.get(project_id=auth.project_id, customer_id=customer_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer_email = memory.data.get("customer_email")
    customer_name = memory.data.get("customer_name")
    
    # Verificar estado en el MCP Calendar Server
    mcp_url = _get_calendar_mcp_url()
    calendar_connected = False
    calendar_email = None
    
    if mcp_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{mcp_url}/oauth/status/{customer_id}")
                if response.status_code == 200:
                    status_data = response.json()
                    calendar_connected = status_data.get("connected", False)
                    calendar_email = status_data.get("calendar_email")
        except Exception:
            # Si falla, usar datos de memoria
            calendar_email = memory.data.get("calendar_email")
            calendar_connected = calendar_email is not None
    
    return CustomerCalendarResponse(
        customer_id=customer_id,
        customer_email=customer_email or "",
        customer_name=customer_name,
        calendar_connected=calendar_connected,
        calendar_email=calendar_email,
    )


@router.get("/list", response_model=CustomerCalendarListResponse)
async def list_customer_calendars(
    auth: AuthContext = Depends(require_auth),
) -> CustomerCalendarListResponse:
    """
    Listar todos los clientes con sus estados de conexión de calendario.
    
    Lista clientes que tienen customer_email en su customer_memory.
    """
    if _memory_store is None:
        raise HTTPException(status_code=500, detail="Memory store not configured")
    
    customers_list: list[CustomerCalendarResponse] = []
    
    # Consultar directamente la base de datos SQLite para obtener todos los customer_ids
    # que tienen customer_email en su memoria
    if isinstance(_memory_store, type) or not hasattr(_memory_store, '_conn'):
        # Si no podemos acceder a la conexión, retornar lista vacía
        return CustomerCalendarListResponse(customers=customers_list)
    
    try:
        import sqlite3
        # Acceder a la conexión SQLite del memory store
        conn = _memory_store._conn
        cur = conn.execute(
            """
            SELECT DISTINCT customer_id, memory_json
            FROM customer_memory
            WHERE project_id = ? AND memory_json LIKE '%customer_email%';
            """,
            (auth.project_id,),
        )
        
        for row in cur.fetchall():
            customer_id = row[0]
            memory_json = row[1]
            
            try:
                import json
                parsed = json.loads(memory_json)
                # El formato es {"slots": {...}, "updated_at": {...}}
                slots = parsed.get("slots", {}) if isinstance(parsed, dict) and "slots" in parsed else (parsed if isinstance(parsed, dict) else {})
                customer_email = slots.get("customer_email")
                customer_name = slots.get("customer_name")
                
                if customer_email:
                    # Verificar estado de conexión en el MCP Calendar Server
                    mcp_url = _get_calendar_mcp_url()
                    calendar_connected = False
                    calendar_email = None
                    
                    if mcp_url:
                        try:
                            async with httpx.AsyncClient(timeout=10.0) as client:
                                response = await client.get(f"{mcp_url}/oauth/status/{customer_id}")
                                if response.status_code == 200:
                                    status_data = response.json()
                                    calendar_connected = status_data.get("connected", False)
                                    calendar_email = status_data.get("calendar_email")
                        except Exception:
                            pass
                    
                    customers_list.append(
                        CustomerCalendarResponse(
                            customer_id=customer_id,
                            customer_email=customer_email,
                            customer_name=customer_name,
                            calendar_connected=calendar_connected,
                            calendar_email=calendar_email,
                        )
                    )
            except Exception:
                continue
    except Exception:
        # Si falla, retornar lista vacía
        pass
    
    return CustomerCalendarListResponse(customers=customers_list)


@router.delete("/disconnect/{customer_id}")
def disconnect_customer_calendar(
    customer_id: str,
    auth: AuthContext = Depends(require_auth),
) -> dict[str, str]:
    """Desconectar Google Calendar de un cliente."""
    if _memory_store is None:
        raise HTTPException(status_code=500, detail="Memory store not configured")
    
    memory = _memory_store.get(project_id=auth.project_id, customer_id=customer_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Remover datos de calendario pero mantener email
    memory_data = memory.data.copy()
    memory_data.pop("calendar_email", None)
    memory_data.pop("calendar_connected", None)
    
    _memory_store.upsert(project_id=auth.project_id, customer_id=customer_id, data=memory_data)
    
    # También desconectar en el MCP Calendar Server
    mcp_url = _get_calendar_mcp_url()
    if mcp_url:
        try:
            import httpx
            with httpx.Client(timeout=10.0) as client:
                client.post(
                    f"{mcp_url}/oauth/disconnect",
                    json={"customer_id": customer_id},
                )
        except Exception:
            pass  # Si falla, continuar (ya se removió de memoria)
    
    return {"message": "Google Calendar desconectado exitosamente", "customer_id": customer_id}
