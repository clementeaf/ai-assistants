#!/usr/bin/env python3
"""Script para probar la comunicación WebSocket simulando frontend-backend."""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import websockets

# Cargar .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Archivo .env cargado")
else:
    print("❌ Archivo .env no encontrado")
    sys.exit(1)

async def test_websocket_chat():
    """Prueba la comunicación WebSocket simulando el frontend."""
    
    # Configuración
    base_url = os.getenv("VITE_API_BASE_URL", "http://localhost:9000")
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    conversation_id = f"test:websocket:{asyncio.get_event_loop().time()}"
    api_key = os.getenv("AI_ASSISTANTS_API_KEY", "")
    customer_id = "+5491112345678"
    
    # Construir URL WebSocket
    ws_endpoint = f"{ws_url}/v1/ws/conversations/{conversation_id}"
    if api_key:
        ws_endpoint += f"?api_key={api_key}"
    if customer_id:
        ws_endpoint += f"&customer_id={customer_id}"
    
    print("\n" + "="*60)
    print("PRUEBA DE COMUNICACIÓN WEBSOCKET")
    print("="*60)
    print(f"URL: {ws_endpoint}")
    print(f"Conversation ID: {conversation_id}")
    print(f"Customer ID: {customer_id}")
    print("="*60 + "\n")
    
    try:
        async with websockets.connect(ws_endpoint) as websocket:
            print("✅ Conexión WebSocket establecida\n")
            
            # Test 1: Enviar "Hola"
            print("[TEST 1] Enviando: 'Hola'")
            print("-" * 60)
            
            message = {
                "type": "user_message",
                "text": "Hola",
                "conversation_id": conversation_id
            }
            
            await websocket.send(json.dumps(message))
            print(f"📤 Enviado: {json.dumps(message, ensure_ascii=False)}")
            
            # Esperar respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 Recibido: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            expected_response = "¡Hola! Buenos días, soy el Asistente IA, ¿qué fecha y hora quisieras consultar para reservar?"
            actual_response = response_data.get("text", "")
            
            print(f"\n✅ Respuesta recibida: {actual_response}")
            if expected_response in actual_response or actual_response == expected_response:
                print(f"✅ RESULTADO: La respuesta es CORRECTA")
            else:
                print(f"❌ RESULTADO: La respuesta NO coincide")
                print(f"   Esperado: {expected_response}")
                print(f"   Recibido: {actual_response}")
            
            # Test 2: Enviar otro "Hola" para verificar que sigue funcionando
            print("\n" + "="*60)
            print("[TEST 2] Enviando: 'Hola' (segunda vez)")
            print("-" * 60)
            
            await websocket.send(json.dumps(message))
            print(f"📤 Enviado: {json.dumps(message, ensure_ascii=False)}")
            
            response2 = await websocket.recv()
            response_data2 = json.loads(response2)
            print(f"📥 Recibido: {json.dumps(response_data2, ensure_ascii=False, indent=2)}")
            
            actual_response2 = response_data2.get("text", "")
            print(f"\n✅ Respuesta recibida: {actual_response2}")
            if expected_response in actual_response2 or actual_response2 == expected_response:
                print(f"✅ RESULTADO: La respuesta es CORRECTA")
            else:
                print(f"❌ RESULTADO: La respuesta NO coincide")
                print(f"   Esperado: {expected_response}")
                print(f"   Recibido: {actual_response2}")
            
            print("\n" + "="*60)
            print("✅ Pruebas completadas")
            print("="*60 + "\n")
            
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ Error: URL WebSocket inválida: {e}")
        print(f"   URL intentada: {ws_endpoint}")
        sys.exit(1)
    except websockets.exceptions.ConnectionRefused as e:
        print(f"❌ Error: No se pudo conectar al servidor")
        print(f"   Verifica que el servidor esté corriendo en {base_url}")
        print(f"   Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_websocket_chat())
