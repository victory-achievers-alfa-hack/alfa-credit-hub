import { randomUUID } from 'node:crypto';
import { WebSocket, WebSocketServer } from 'ws';

const port = Number(process.env.WS_PORT ?? 8080);
const allowedEvents = new Set([
  'application.updated',
  'notification.created',
  'notification.read',
]);

const server = new WebSocketServer({ port, maxPayload: 1024 * 1024 });

function send(socket, message) {
  if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(message));
}

function broadcast(sender, message) {
  server.clients.forEach((client) => {
    if (client !== sender) send(client, message);
  });
}

server.on('connection', (socket) => {
  const clientId = randomUUID();
  socket.isAlive = true;

  send(socket, {
    id: randomUUID(),
    sentAt: new Date().toISOString(),
    type: 'connection.ready',
    payload: { clientId },
  });

  socket.on('pong', () => {
    socket.isAlive = true;
  });

  socket.on('message', (rawMessage) => {
    try {
      const message = JSON.parse(rawMessage.toString());
      if (!message || !allowedEvents.has(message.type) || !message.payload) return;

      broadcast(socket, {
        ...message,
        id: typeof message.id === 'string' ? message.id : randomUUID(),
        sentAt: typeof message.sentAt === 'string' ? message.sentAt : new Date().toISOString(),
      });
    } catch {
      send(socket, {
        id: randomUUID(),
        sentAt: new Date().toISOString(),
        type: 'connection.error',
        payload: { message: 'Некорректный формат realtime-события' },
      });
    }
  });
});

const heartbeat = setInterval(() => {
  server.clients.forEach((socket) => {
    if (!socket.isAlive) {
      socket.terminate();
      return;
    }
    socket.isAlive = false;
    socket.ping();
  });
}, 30_000);

server.on('listening', () => {
  console.log(`[realtime] WebSocket relay started on ws://localhost:${port}`);
});

function shutdown() {
  clearInterval(heartbeat);
  server.close(() => process.exit(0));
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
