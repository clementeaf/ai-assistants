#!/usr/bin/env node
/**
 * WhatsApp Baileys Service
 * Servicio Node.js que usa Baileys para conectarse a WhatsApp Web
 * y se integra con el backend Python FastAPI
 */

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const pino = require('pino');
const axios = require('axios');
const qrcode = require('qrcode-terminal');
const QRCode = require('qrcode');
const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

// Cargar variables de entorno desde .env (desde el directorio del script)
require('dotenv').config({ path: path.join(__dirname, '.env') });

// Logger (debe estar antes de usarlo)
const logger = pino({ level: 'info' });

// Configuración
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API_KEY = process.env.API_KEY || process.env.AI_ASSISTANTS_API_KEY || 'dev';
const WHATSAPP_AUTH_DIR = process.env.WHATSAPP_AUTH_DIR || path.join(__dirname, 'auth_info');
const PORT = process.env.PORT || 60007;

// WHITELIST: Solo números autorizados pueden interactuar con el bot
// Format: números separados por coma sin espacios (ej: "56959263366,56912345678")
const ALLOWED_NUMBERS = process.env.ALLOWED_NUMBERS 
  ? process.env.ALLOWED_NUMBERS.split(',').map(n => n.trim()).filter(n => n.length > 0)
  : [];

// SEGURIDAD: Si ALLOWED_NUMBERS está vacío, NO responder a NADIE
if (ALLOWED_NUMBERS.length === 0) {
  logger.warn('⚠️  ALLOWED_NUMBERS está vacío. El bot NO responderá a ningún número por seguridad.');
} else {
  logger.info({ 
    allowedNumbers: ALLOWED_NUMBERS,
    count: ALLOWED_NUMBERS.length 
  }, '✅ Whitelist de números autorizados cargada');
}

const TEST_NUMBER = process.env.TEST_NUMBER;

// Servidor web para mostrar QR
const app = express();

// CORS usando el paquete cors instalado - debe estar antes de todas las rutas
app.use(cors({
  origin: true, // Permitir cualquier origen
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Accept', 'X-Requested-With'],
  credentials: false,
  preflightContinue: false,
  optionsSuccessStatus: 204
}));

let currentQR = null;
let isConnected = false;

// Asegurar que el directorio de autenticación existe
if (!fs.existsSync(WHATSAPP_AUTH_DIR)) {
  fs.mkdirSync(WHATSAPP_AUTH_DIR, { recursive: true });
}

/**
 * Envía un mensaje interactivo con botones (máximo 3 botones)
 * Formato Baileys para botones interactivos
 * SEGURIDAD: Esta función solo se llama después de verificar la whitelist
 */
async function sendInteractiveButtons(sock, to, text, buttons) {
  // Extraer número del destinatario para logging de seguridad
  const toNumber = to ? to.replace('@s.whatsapp.net', '').replace('@c.us', '') : 'unknown';
  
  // Verificación adicional de seguridad (doble verificación)
  if (ALLOWED_NUMBERS.length > 0 && !ALLOWED_NUMBERS.includes(toNumber)) {
    logger.error({ 
      toNumber, 
      allowedNumbers: ALLOWED_NUMBERS,
      reason: 'Intento de enviar mensaje a número no autorizado - BLOQUEADO'
    }, '🚫 SEGURIDAD: Intento de enviar botones a número no autorizado');
    return; // NO ENVIAR
  }
  
  // Máximo 3 botones en WhatsApp
  const buttonList = buttons.slice(0, 3).map((btn, idx) => {
    const buttonText = typeof btn === 'string' ? btn : (btn.text || btn.title || `Botón ${idx + 1}`);
    return {
      buttonId: `btn_${idx + 1}`,
      buttonText: { displayText: buttonText },
      type: 1 // Tipo 1 = botón de respuesta rápida
    };
  });

  await sock.sendMessage(to, {
    text: text,
    buttons: buttonList,
    footer: ''
  });
  
  logger.info({ to: toNumber, buttons: buttonList.length }, '✅ Mensaje interactivo con botones enviado (número autorizado)');
}

/**
 * Envía un mensaje interactivo con lista
 */
async function sendInteractiveList(sock, to, text, listTitle, listItems) {
  // Máximo 10 items en una lista de WhatsApp
  const items = listItems.slice(0, 10).map((item, idx) => ({
    title: typeof item === 'string' ? item : (item.title || `Opción ${idx + 1}`),
    description: typeof item === 'object' && item.description ? item.description : '',
    rowId: `row_${idx + 1}`
  }));

  const sections = [{
    title: listTitle || 'Selecciona una opción',
    rows: items
  }];

  await sock.sendMessage(to, {
    text: text,
    sections: sections,
    title: listTitle || 'Menú',
    buttonText: 'Ver opciones'
  });
}

/**
 * Envía un mensaje al backend Python
 */
async function sendToBackend(fromNumber, text, messageId, timestamp, pushName = null) {
  try {
    const payload = {
      message_id: messageId || `msg-${Date.now()}`,
      from_number: fromNumber,
      text: text,
      timestamp_iso: timestamp || new Date().toISOString(),
      customer_name: pushName, // Nombre del usuario de WhatsApp
    };

    const headers = {
      'Content-Type': 'application/json',
    };

    // Agregar autenticación si está configurada
    if (API_KEY && API_KEY !== 'dev') {
      headers['X-API-Key'] = API_KEY;
    }

    const response = await axios.post(
      `${BACKEND_URL}/v1/channels/whatsapp/gateway/inbound`,
      payload,
      { headers }
    );

    return response.data;
  } catch (error) {
    logger.error({ error: error.message, stack: error.stack }, 'Error enviando mensaje al backend');
    throw error;
  }
}

// Variable global para el socket (para poder enviar mensajes de prueba)
let globalSock = null;

// Cache de mensajes procesados para evitar duplicados
const processedMessages = new Set();
const MESSAGE_CACHE_TTL = 60000; // 60 segundos

/**
 * Limpia mensajes antiguos del cache
 */
function cleanMessageCache() {
  // El Set se limpia automáticamente, pero podemos limitar su tamaño
  if (processedMessages.size > 1000) {
    // Si hay más de 1000 mensajes, limpiar la mitad más antigua
    const messagesArray = Array.from(processedMessages);
    const toRemove = messagesArray.slice(0, 500);
    toRemove.forEach(msgId => processedMessages.delete(msgId));
  }
}

// Limpiar cache cada 5 minutos
setInterval(cleanMessageCache, 5 * 60 * 1000);

// Endpoint JSON para obtener el estado (para el frontend)
app.get('/status', (req, res) => {
  res.json({
    connected: isConnected,
    qr: currentQR ? `data:image/png;base64,${currentQR}` : null
  });
});

// Configurar servidor web para mostrar QR
app.get('/', (req, res) => {
  if (isConnected) {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>WhatsApp Baileys Service</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 500px;
          }
          .status {
            color: #25D366;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
          }
          .info {
            color: #666;
            line-height: 1.6;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="status">Conectado a WhatsApp</div>
          <div class="info">
            <p>El servicio está conectado y funcionando correctamente.</p>
            <p>Puedes enviar mensajes de WhatsApp y serán procesados por el asistente de IA.</p>
          </div>
        </div>
      </body>
      </html>
    `);
  } else if (currentQR) {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Escanea el código QR - WhatsApp Baileys</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 500px;
          }
          h1 {
            color: #25D366;
            margin-bottom: 20px;
          }
          .qr-container {
            margin: 30px 0;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 10px;
          }
          .qr-container img {
            max-width: 100%;
            height: auto;
          }
          .instructions {
            color: #666;
            line-height: 1.6;
            margin-top: 20px;
          }
          .instructions ol {
            text-align: left;
            display: inline-block;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Conectar WhatsApp</h1>
          <div class="qr-container">
            <img src="data:image/png;base64,${currentQR}" alt="QR Code">
          </div>
          <div class="instructions">
            <p><strong>Instrucciones:</strong></p>
            <ol>
              <li>Abre WhatsApp en tu teléfono</li>
              <li>Ve a <strong>Configuración → Dispositivos vinculados</strong></li>
              <li>Presiona <strong>"Vincular un dispositivo"</strong></li>
              <li>Escanea este código QR</li>
            </ol>
            <p style="margin-top: 20px; color: #999; font-size: 14px;">
              Esta página se actualiza automáticamente. Una vez conectado, verás un mensaje de confirmación.
            </p>
          </div>
        </div>
        <script>
          // Auto-refresh cada 2 segundos para actualizar el estado
          setTimeout(() => location.reload(), 2000);
        </script>
      </body>
      </html>
    `);
  } else {
    res.send(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>WhatsApp Baileys Service</title>
        <meta charset="utf-8">
        <style>
          body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>⏳ Esperando código QR...</h1>
          <p>El servicio se está iniciando. Esta página se actualizará automáticamente.</p>
        </div>
        <script>
          setTimeout(() => location.reload(), 2000);
        </script>
      </body>
      </html>
    `);
  }
});

/**
 * Envía un mensaje de prueba a un número
 * DESHABILITADO POR SEGURIDAD - No usar esta función
 */
async function sendTestMessage(number, message) {
  // FUNCIÓN DESHABILITADA POR SEGURIDAD
  // No se permite enviar mensajes automáticos para prevenir spam
  logger.warn({ 
    number, 
    reason: 'sendTestMessage está deshabilitada por seguridad' 
  }, '⚠️  Intento de enviar mensaje de prueba bloqueado');
  return;
}

/**
 * Inicializa y conecta WhatsApp usando Baileys
 */
async function connectWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(WHATSAPP_AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    logger: pino({ level: 'silent' }),
    auth: state,
    browser: ['AI Assistants', 'Chrome', '1.0.0'],
  });

  globalSock = sock;

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      logger.info('Escanea el código QR con WhatsApp para conectar');
      qrcode.generate(qr, { small: true });
      
      // Generar QR como imagen base64 para la web
      try {
        const qrImage = await QRCode.toDataURL(qr);
        currentQR = qrImage.split(',')[1]; // Remover el prefijo data:image/png;base64,
        isConnected = false;
        logger.info(`Código QR disponible en: http://localhost:${PORT}`);
      } catch (error) {
        logger.error({ error: error.message }, 'Error generando QR para web');
      }
    }

    if (connection === 'close') {
      isConnected = false;
      currentQR = null;
      const statusCode = (lastDisconnect?.error)?.output?.statusCode;
      const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
      
      logger.info({ shouldReconnect, statusCode, error: lastDisconnect?.error }, 'Conexión cerrada');

      // Si hay error 401 (credenciales inválidas), eliminar credenciales para forzar nuevo QR
      let forceReconnect = false;
      if (statusCode === 401) {
        logger.warn('Credenciales inválidas (401). Eliminando credenciales para generar nuevo QR...');
        try {
          const credsFiles = ['creds.json', 'app-state-sync-key.json', 'app-state-sync-version.json', 'pre-key.json', 'session.json', 'sender-key.json'];
          credsFiles.forEach(file => {
            const filePath = path.join(WHATSAPP_AUTH_DIR, file);
            if (fs.existsSync(filePath)) {
              fs.unlinkSync(filePath);
              logger.info({ file }, 'Credencial eliminada');
            }
          });
          forceReconnect = true; // Forzar reconexión después de eliminar credenciales
        } catch (error) {
          logger.error({ error: error.message }, 'Error eliminando credenciales');
        }
      }

      if (shouldReconnect || forceReconnect) {
        logger.info('Reconectando...');
        // Esperar un poco antes de reconectar para que se procese la eliminación de credenciales
        setTimeout(() => {
          connectWhatsApp();
        }, 2000);
      }
    } else if (connection === 'open') {
      isConnected = true;
      currentQR = null;
      logger.info('✅ Conectado a WhatsApp Web');
      
      // NO ENVIAR MENSAJES AUTOMÁTICOS - comentado para prevenir spam
      // if (TEST_NUMBER) {
      //   setTimeout(async () => {
      //     await sendTestMessage(
      //       TEST_NUMBER,
      //       'Hola! Este es un mensaje de prueba del servicio de WhatsApp Baileys. El servicio está funcionando correctamente y listo para recibir mensajes.'
      //     );
      //   }, 3000);
      // }
    }
  });

  // Escuchar mensajes entrantes
  sock.ev.on('messages.upsert', async (m) => {
    const messages = m.messages;
    logger.info({ messageCount: messages.length, type: m.type }, 'Evento messages.upsert recibido');
    
    // CRÍTICO: Solo procesar mensajes nuevos (type 'notify'), NO historial
    if (m.type !== 'notify') {
      logger.debug({ type: m.type }, 'Ignorando mensajes no-notify (historial)');
      return;
    }
    
    // Obtener nuestro número de WhatsApp
    const ourJid = sock.user?.id || null;
    const ourNumberFull = ourJid ? ourJid.split('@')[0] : null;
    // Extraer solo el número sin el dispositivo (remover :64, :65, etc.)
    const ourNumber = ourNumberFull ? ourNumberFull.split(':')[0] : null;
    
    for (const msg of messages) {
      const remoteJid = msg.key.remoteJid;
      // Extraer el número del remoteJid (remover @s.whatsapp.net, @c.us, etc.)
      const remoteNumber = remoteJid ? remoteJid.split('@')[0] : null;
      const isToSelf = ourNumber && remoteNumber && remoteNumber === ourNumber;
      
      // Capturar el nombre del usuario de WhatsApp (si está disponible)
      const pushName = msg.pushName || null;
      
      logger.info({ 
        fromMe: msg.key.fromMe, 
        remoteJid, 
        ourNumber, 
        isToSelf,
        pushName,
        hasMessage: !!msg.message 
      }, 'Procesando mensaje');
      
        // IGNORAR mensajes propios EXCEPTO si son mensajes enviados a nuestro propio número (isToSelf)
        // IMPORTANTE: Aún así, debe pasar por la whitelist
        if (msg.key.fromMe && !isToSelf) {
          logger.debug({ from: remoteJid }, 'Mensaje propio ignorado (no es para nosotros)');
          continue;
        }
        
        // Si es mensaje propio pero es para nuestro número, procesarlo
        // NOTA: Aún debe pasar por la whitelist más abajo
        if (msg.key.fromMe && isToSelf) {
          logger.info({ from: remoteJid }, 'Mensaje propio recibido (enviado a nuestro número) - Verificando whitelist...');
        }

      let text = null;
      
      // Extraer texto de diferentes tipos de mensajes
      if (msg.message?.conversation) {
        text = msg.message.conversation;
      } else if (msg.message?.extendedTextMessage?.text) {
        text = msg.message.extendedTextMessage.text;
      } else if (msg.message?.ephemeralMessage?.message?.conversation) {
        text = msg.message.ephemeralMessage.message.conversation;
      } else if (msg.message?.viewOnceMessage?.message?.conversation) {
        text = msg.message.viewOnceMessage.message.conversation;
      }

      logger.info({ text, hasText: !!text, messageKeys: Object.keys(msg.message || {}) }, 'Texto extraído del mensaje');

      if (!text) {
        logger.info({ remoteJid, messageType: Object.keys(msg.message || {}) }, 'Mensaje sin texto, ignorando');
        continue; // Ignorar mensajes que no son de texto
      }

      const from = msg.key.remoteJid;
      const messageId = msg.key.id;
      const timestamp = msg.messageTimestamp ? new Date(msg.messageTimestamp * 1000).toISOString() : new Date().toISOString();

        // Crear ID único para el mensaje (combinar messageId + from + timestamp)
        const uniqueMessageId = `${messageId}-${from}-${timestamp}`;
        
        // Verificar si el mensaje ya fue procesado
        if (processedMessages.has(uniqueMessageId)) {
          logger.debug({ messageId, from }, 'Mensaje ya procesado, ignorando');
          continue;
        }

        // Marcar mensaje como procesado
        processedMessages.add(uniqueMessageId);

        // Extraer número de teléfono (remover @s.whatsapp.net, @c.us, @g.us)
        let fromNumber = from;
        if (from.includes('@s.whatsapp.net')) {
          fromNumber = from.replace('@s.whatsapp.net', '');
        } else if (from.includes('@c.us')) {
          fromNumber = from.replace('@c.us', '');
        } else if (from.includes('@g.us')) {
          // IGNORAR GRUPOS COMPLETAMENTE
          logger.info({ from }, 'Mensaje de grupo ignorado');
          continue;
        }

        // WHITELIST: Verificar que el número esté autorizado
        // SEGURIDAD CRÍTICA: Si ALLOWED_NUMBERS está vacío, NO responder a NADIE
        if (ALLOWED_NUMBERS.length === 0) {
          logger.warn({ 
            fromNumber,
            reason: 'ALLOWED_NUMBERS está vacío - Modo seguro activado'
          }, '⚠️  Mensaje BLOQUEADO - Whitelist vacía (modo seguro)');
          continue;
        }
        
        // Verificar que el número esté en la whitelist
        if (!ALLOWED_NUMBERS.includes(fromNumber)) {
          logger.warn({ 
            fromNumber, 
            allowedNumbers: ALLOWED_NUMBERS,
            reason: 'Número no está en whitelist'
          }, '🚫 Número NO autorizado - Mensaje BLOQUEADO');
          continue;
        }

        logger.info({ from: fromNumber, pushName, text, isAllowed: true }, 'Mensaje recibido de número autorizado');

        try {
          // Enviar al backend Python
          const response = await sendToBackend(fromNumber, text, messageId, timestamp, pushName);

          // Enviar respuesta del backend a WhatsApp
          // SEGURIDAD: Verificar whitelist ANTES de enviar cualquier mensaje
          if (response.response_text) {
            // Verificación adicional de seguridad antes de enviar
            if (ALLOWED_NUMBERS.length > 0 && !ALLOWED_NUMBERS.includes(fromNumber)) {
              logger.error({ 
                fromNumber, 
                allowedNumbers: ALLOWED_NUMBERS,
                reason: 'Intento de enviar respuesta a número no autorizado - BLOQUEADO'
              }, '🚫 SEGURIDAD: Intento de enviar respuesta a número no autorizado');
              return; // NO ENVIAR
            }
            
            // Verificar si el backend quiere enviar un mensaje interactivo
            if (response.interactive_type === 'buttons' && response.buttons) {
              await sendInteractiveButtons(sock, from, response.response_text, response.buttons);
            } else if (response.interactive_type === 'list' && response.list_items) {
              await sendInteractiveList(sock, from, response.response_text, response.list_title, response.list_items);
            } else {
              // Mensaje de texto normal
              // Verificación adicional de seguridad (doble verificación)
              if (ALLOWED_NUMBERS.length > 0 && !ALLOWED_NUMBERS.includes(fromNumber)) {
                logger.error({ 
                  fromNumber, 
                  allowedNumbers: ALLOWED_NUMBERS,
                  reason: 'Intento de enviar mensaje de texto a número no autorizado - BLOQUEADO'
                }, '🚫 SEGURIDAD: Intento de enviar mensaje de texto a número no autorizado');
                return; // NO ENVIAR
              }
              
              await sock.sendMessage(from, { text: response.response_text });
              logger.info({ to: fromNumber, text: response.response_text }, '✅ Respuesta enviada (número autorizado)');
            }
          }
        } catch (error) {
          logger.error({ error: error.message, stack: error.stack }, 'Error procesando mensaje');
          // NO enviar mensaje de error automático para evitar spam
          // Si el backend falla, simplemente loguear el error
        }
    }
  });

  return sock;
}

// Iniciar servicio
async function start() {
  logger.info({ backend: BACKEND_URL, port: PORT }, 'Iniciando WhatsApp Baileys Service');
  
  // Iniciar servidor web
  app.listen(PORT, () => {
    logger.info(`Servidor web iniciado en http://localhost:${PORT}`);
    logger.info(`Abre http://localhost:${PORT} en tu navegador para escanear el código QR`);
  });
  
  try {
    await connectWhatsApp();
    logger.info('Servicio iniciado correctamente');
  } catch (error) {
    logger.error({ error: error.message, stack: error.stack }, 'Error iniciando servicio');
    process.exit(1);
  }
}

// Manejar cierre graceful
process.on('SIGINT', () => {
  logger.info('Cerrando servicio...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  logger.info('Cerrando servicio...');
  process.exit(0);
});

// Iniciar
start();
