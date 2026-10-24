# Альфа / Поток — frontend

Кредитный кабинет предпринимателя и рабочее место сотрудника банка.

## Стек

- React 19
- TypeScript
- Vite
- React Router
- `@alfalab/core-components`
- аутентифицированный backend WebSocket с reconnect и polling fallback

## Запуск

Сначала запустите backend на `127.0.0.1:8000`. Затем:

```bash
npm install
npm run dev
```

Vite проксирует `/api` и WebSocket на backend. Переменные для отдельного origin:

```env
VITE_API_URL=https://example.ru/api/v1
VITE_WS_URL=wss://example.ru/api/v1/realtime
```

`npm run realtime` запускает только старый изолированный demo-relay и основному приложению не требуется.

Проверки:

```bash
npm run lint
npm run build
npm run realtime:test
```

## Демо-аккаунты

Пароль для всех аккаунтов: `123456`.

| Роль | Логин | Профиль |
|---|---|---|
| Клиент | `client@demo.ru` | Магазин «Город» |
| Клиент | `cafe@demo.ru` | Кофейня «Зёрна» |
| Клиент | `vector@demo.ru` | ООО «Вектор» |
| Банк | `bank@demo.ru` | Андеррайтер |

## Маршруты

### Клиент

- `/client` — главная и финансовый обзор
- `/client/business` — профиль компании и документы
- `/client/financing` — подбор кредитного продукта
- `/client/apply` — подтверждение и отправка заявки
- `/client/applications` — список заявок
- `/client/applications/:id` — статус, оффер, подписание и выдача

### Банк

- `/bank` — очередь заявок
- `/bank/applications/:id` — проверки, скоринг и банковское решение

## Текущее хранение данных

Пользователи, компании, продукты, заявки, решения, события и уведомления загружаются из backend. Браузерное хранилище больше не является источником бизнес-состояния.

- авторизация — HttpOnly-cookie;
- восстановление сессии — `GET /api/v1/me`;
- изменения — backend WebSocket `/api/v1/realtime`;
- резервная синхронизация — polling активной вкладки раз в 15 секунд;
- вход/выход синхронизируются между вкладками через `BroadcastChannel`.

Cookie общая для вкладок одного browser profile. Для параллельной демонстрации клиента и банка используйте разные профили браузера или инкогнито.

## Что уже сделано и что нужно от команды

Полная передача frontend, список реализованных функций и ожидания от backend и аналитика находятся в [корневом README](../README.md).

Требования к интеграции описаны в [`INTEGRATION.md`](./INTEGRATION.md).
