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
const path = require('path');
const fs = require('fs');

// Configuración
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const API_KEY = process.env.API_KEY || process.env.AI_ASSISTANTS_API_KEY || 'dev';
const WHATSAPP_AUTH_DIR = process.env.WHATSAPP_AUTH_DIR || path.join(__dirname, 'auth_info');
const PORT = process.env.PORT || 60007;
const TEST_NUMBER = process.env.TEST_NUMBER;

// Servidor web para mostrar QR
const app = express();
let currentQR = null;
let isConnected = false;

// Logger
const logger = pino({ level: 'info' });

// Asegurar que el directorio de autenticación existe
if (!fs.existsSync(WHATSAPP_AUTH_DIR)) {
  fs.mkdirSync(WHATSAPP_AUTH_DIR, { recursive: true });
}

/**
 * Envía un mensaje al backend Python
 */
async function sendToBackend(fromNumber, text, messageId, timestamp) {
  try {
    const payload = {
      message_id: messageId || `msg-${Date.now()}`,
      from_number: fromNumber,
      text: text,
      timestamp_iso: timestamp || new Date().toISOString(),
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
          <div class="status">✅ Conectado a WhatsApp</div>
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
          <h1>🔗 Conectar WhatsApp</h1>
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
 */
async function sendTestMessage(number, message) {
  if (!globalSock) {
    logger.warn('Socket no está disponible aún');
    return;
  }

  try {
    const jid = `${number}@s.whatsapp.net`;
    await globalSock.sendMessage(jid, { text: message });
    logger.info({ to: number, message }, 'Mensaje de prueba enviado');
  } catch (error) {
    logger.error({ error: error.message, number }, 'Error enviando mensaje de prueba');
  }
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
      const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
      logger.info({ shouldReconnect, error: lastDisconnect?.error }, 'Conexión cerrada');

      if (shouldReconnect) {
        logger.info('Reconectando...');
        connectWhatsApp();
      }
    } else if (connection === 'open') {
      isConnected = true;
      currentQR = null;
      logger.info('✅ Conectado a WhatsApp Web');
      
      // Enviar mensaje de prueba si TEST_NUMBER está configurado
      if (TEST_NUMBER) {
        setTimeout(async () => {
          await sendTestMessage(
            TEST_NUMBER,
            'Hola! Este es un mensaje de prueba del servicio de WhatsApp Baileys. El servicio está funcionando correctamente y listo para recibir mensajes.'
          );
        }, 3000); // Esperar 3 segundos después de conectar
      }
    }
  });

  // Escuchar mensajes entrantes
  sock.ev.on('messages.upsert', async (m) => {
    const messages = m.messages;
    
    for (const msg of messages) {
      // Solo procesar mensajes de texto nuevos (no historial)
      // También procesar mensajes con texto extendido (ephemeralMessage, viewOnceMessage, etc.)
      if (m.type === 'notify') {
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

        if (!text) {
          continue; // Ignorar mensajes que no son de texto
        }

        const from = msg.key.remoteJid;
        const messageId = msg.key.id;
        const timestamp = msg.messageTimestamp ? new Date(msg.messageTimestamp * 1000).toISOString() : new Date().toISOString();

        // Extraer número de teléfono (remover @s.whatsapp.net, @c.us, @g.us)
        let fromNumber = from;
        if (from.includes('@s.whatsapp.net')) {
          fromNumber = from.replace('@s.whatsapp.net', '');
        } else if (from.includes('@c.us')) {
          fromNumber = from.replace('@c.us', '');
        } else if (from.includes('@g.us')) {
          // Es un grupo, extraer el número del remitente real
          const participant = msg.key.participant;
          if (participant) {
            fromNumber = participant.replace('@s.whatsapp.net', '').replace('@c.us', '');
          } else {
            logger.warn({ from }, 'Mensaje de grupo sin participante, ignorando');
            continue;
          }
        }

        logger.info({ from: fromNumber, text }, 'Mensaje recibido');

        try {
          // Enviar al backend Python
          const response = await sendToBackend(fromNumber, text, messageId, timestamp);

          // Enviar respuesta del backend a WhatsApp
          if (response.response_text) {
            await sock.sendMessage(from, { text: response.response_text });
            logger.info({ to: fromNumber, text: response.response_text }, 'Respuesta enviada');
          }
        } catch (error) {
          logger.error({ error: error.message, stack: error.stack }, 'Error procesando mensaje');
          // Enviar mensaje de error al usuario
          try {
            await sock.sendMessage(from, {
              text: 'Lo siento, hubo un error procesando tu mensaje. Por favor intenta más tarde.',
            });
          } catch (sendError) {
            logger.error({ error: sendError.message }, 'Error enviando mensaje de error');
          }
        }
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
