# Альфа / Поток — frontend

Кредитный кабинет предпринимателя и рабочее место сотрудника банка.

## Стек

- React 19
- TypeScript
- Vite
- React Router
- `@alfalab/core-components`
- WebSocket (`ws`) для realtime-демо

## Запуск

```bash
npm install
```

В первом терминале запустите realtime relay:

```bash
npm run realtime
```

Во втором терминале запустите frontend:

```bash
npm run dev
```

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

До подключения backend приложение использует браузерное хранилище:

- `alfa_stream_user_v2` в `sessionStorage` — активный пользователь текущей вкладки;
- `alfa_stream_applications_v2` в `localStorage` — заявки и история переходов;
- `alfa_stream_notifications_v1` в `localStorage` — клиентские уведомления и признак прочтения.

Изменения заявок и уведомлений синхронизируются между вкладками через `storage`, а между разными браузерами — через локальный WebSocket relay `ws://localhost:8080`.

Кнопка «Сбросить демо» в банковском кабинете возвращает исходные сценарии.

## Что уже сделано и что нужно от команды

Полная передача frontend, список реализованных функций и ожидания от backend и аналитика находятся в [корневом README](../README.md).

Требования к интеграции описаны в [`INTEGRATION.md`](./INTEGRATION.md).
