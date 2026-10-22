# Realtime relay

Минимальный WebSocket relay для локальной демонстрации. Он не хранит данные и только пересылает типизированные события другим подключённым клиентам.

## Запуск

```bash
npm run realtime
```

По умолчанию сервер слушает `ws://localhost:8080`. Другой порт можно передать через переменную `WS_PORT`.

Поддерживаемые события:

- `application.updated`
- `notification.created`
- `notification.read`

Это demo-инфраструктура без авторизации. В production соединение должен аутентифицировать backend или API gateway.
