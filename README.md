# Альфа / Поток

Демонстрационный кредитный кабинет предпринимателя и рабочее место сотрудника банка. Приложение показывает полный путь от подбора продукта до решения банка, подписания и моделируемой выдачи.

## Архитектура

```text
React + TypeScript frontend
          │ HTTP / WebSocket
          ▼
      FastAPI backend
          │
          ▼
 SQLAlchemy + SQLite
```

Backend является источником истины для пользователей, компаний, продуктов, заявок, решений, уведомлений и расчётов. Frontend хранит только UI-состояние, подписи, список демонстрационных аккаунтов и статические новости.

## Что реализовано

- роли клиента и сотрудника банка;
- авторизация через HttpOnly-cookie или Bearer token;
- профиль компании и синтетические документы;
- каталог продуктов и grouped recommendations;
- rule-based scoring, расчёт платежа и покрытия;
- создание заявки и контролируемые переходы статусов;
- решения `approve`, `alternative`, `need_info`, `reject`;
- принятие оффера, демоподписание и моделируемая выдача;
- уведомления, аутентифицированный WebSocket и polling fallback;
- Swagger/OpenAPI, Docker Compose и автоматические тесты.

## Структура репозитория

| Путь | Назначение |
|---|---|
| `backend/main.py` | FastAPI-приложение и startup-инициализация БД. |
| `backend/src/api/` | HTTP/WebSocket-роуты. |
| `backend/src/service/` | Бизнес-сценарии и работа с заявками. |
| `backend/src/schemas/` | Публичные Pydantic DTO. |
| `backend/src/scoring/` | Scoring, financing, ranking и stress-расчёты. |
| `backend/src/models.py` | SQLAlchemy-модели. |
| `backend/src/seed.py` | Демонстрационные данные для пустой БД. |
| `frontend/src/` | React-приложение. |
| `tests/`, `backend/tests/` | Расчётные, API- и workflow-тесты. |
| `examples/financing_demo.py` | Воспроизводимый пример финансового расчёта. |
| `docs/CONTRACTS.md` | Единый API-, realtime- и decisioning-контракт. |
| `docker-compose.yml` | Локальный запуск frontend и backend. |

## Быстрый запуск через Docker

```bash
docker compose up --build
```

После запуска:

- приложение: `http://localhost`;
- API: `http://localhost:8000/api/v1`;
- Swagger: `http://localhost:8000/docs`;
- healthcheck: `http://localhost:8000/api/v1/health`.

SQLite хранится в Docker volume `backend-data`. При первом запуске пустая БД автоматически заполняется demo-данными.

## Локальная разработка

Требуются Python 3.12+, [uv](https://docs.astral.sh/uv/) и Node.js 20+.

### Backend

```bash
uv sync --group test
uv run uvicorn backend.main:app --reload
```

Backend будет доступен на `http://localhost:8000`.

### Frontend

В другом терминале:

```bash
cd frontend
npm ci
npm run dev
```

Frontend будет доступен на `http://localhost:5173`. Vite проксирует `/api` и WebSocket на `http://127.0.0.1:8000`.

Для разных origin поддерживаются:

```env
VITE_API_URL=https://example.ru/api/v1
VITE_WS_URL=wss://example.ru/api/v1/realtime
```

## Демо-аккаунты

Пароль для всех аккаунтов: `123456`.

| Роль | Логин | Профиль |
|---|---|---|
| Клиент | `client@demo.ru` | Магазин «Город» |
| Клиент | `cafe@demo.ru` | Кофейня «Зёрна» |
| Клиент | `vector@demo.ru` | ООО «Вектор» |
| Банк | `bank@demo.ru` | Андеррайтер |

Cookie общая для вкладок одного browser profile. Для одновременной проверки клиента и банка используйте обычное окно и инкогнито либо два разных профиля браузера.

## Основные маршруты

### Клиент

- `/client` — финансовый обзор;
- `/client/business` — компания и документы;
- `/client/financing` — подбор продукта;
- `/client/apply` — отправка заявки;
- `/client/applications` — список заявок;
- `/client/applications/:id` — статус и действия по заявке.

### Банк

- `/bank` — очередь заявок;
- `/bank/applications/:id` — проверки, scoring и решение.

## Проверки

Из корня проекта:

```bash
uv run --group test pytest -q -p no:cacheprovider
uv run python -m examples.financing_demo
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Локальные генерируемые файлы

Эти файлы не входят в Git и могут быть пересозданы:

- `.venv/` — Python-зависимости;
- `frontend/node_modules/` — npm-зависимости;
- `frontend/dist/` — production-сборка;
- `.pytest_cache/`, `__pycache__/` — кэши Python;
- `alfa-credit-hub.db` — локальная SQLite с demo-состоянием.

Удаление локальной БД сбрасывает заявки и повторно создаёт seed-данные при следующем запуске backend.

## Контракты и ограничения

Единственный актуальный технический документ — [`docs/CONTRACTS.md`](./docs/CONTRACTS.md). Runtime-схемы DTO доступны в `/openapi.json`; при расхождении они имеют приоритет.

Перед production остаются PostgreSQL и миграции, production secrets/CORS, защита demo endpoint’ов, гарантированная realtime-доставка между несколькими процессами, идемпотентность и доработка части бизнес-правил. Полный список зафиксирован в контракте.
