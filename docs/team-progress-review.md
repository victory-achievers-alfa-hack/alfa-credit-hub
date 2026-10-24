# Сверка результата команды и остаток до MVP

Состояние на 24 октября 2026, база аудита — `main` на коммите `8a783d5` плюс frontend-исправления после проверки интеграции.

## Резюме

Команда закрыла большую часть технического MVP:

- backend хранит данные и управляет кредитным процессом;
- frontend переключён с demo-store на серверный API;
- добавлен объяснимый deterministic scoring, финансовая оценка, ранжирование и stress-функция;
- реализованы cookie-auth, роли, заявки, решения, уведомления и WebSocket;
- появились Docker Compose, seed и 52 заявленных командой теста.

Это уже интегрированный демонстрационный контур, но не production-ready система. Основные незакрытые зоны: deployment стенда, безопасность demo endpoint'ов и секретов, миграции/PostgreSQL, полнота realtime, загрузка новых документов, конкурентные операции и полноценный ML lifecycle.

## Что сделал backend-разработчик

### Выполнено

| Задача | Статус | Реализация |
|---|---|---|
| Модели и хранение | Готово для MVP | Пользователи, компании, продукты, заявки, checks, решения, события, уведомления и аудит в `backend/src/models.py` |
| Seed | Готово | Три компании, продукты, четыре пользователя и заявки в `backend/src/seed.py` |
| Auth и роли | Готово для demo | PBKDF2, подписанный токен, HttpOnly-cookie/Bearer, роли client/bank в `backend/src/auth.py` и `backend/src/dependency.py` |
| Профиль и каталог | Готово | `/companies/me`, `/credit-products` |
| Рекомендации | Готово | Строгий grouped response и RecommendationAudit |
| Заявки клиента | Готово | Создание, список, карточка, сведения, accept, sign, disburse |
| Банковская очередь | Готово | Список, карточка и approve/alternative/need_info/reject |
| State machine | Готово | Централизована в `backend/src/service/application_state.py` |
| Уведомления | Готово для MVP | Список, read, создание после решения |
| WebSocket | Частично готово | Аутентификация и фильтрация по пользователю/компании/роли |
| Ошибки | В основном готово | Общий плоский формат для основных FastAPI exceptions |
| Docker | Готово для demo | Backend image, Compose, SQLite volume, healthcheck, Nginx proxy |
| Тесты | Хорошая база | Lifecycle/auth API-тесты и отдельные scoring/financing/ranking/stress тесты |

### Частично или не выполнено

1. `application.updated` отправляется после банковского решения, но не после создания заявки, ответа на `need_info`, accept, sign и disburse.
2. Клиент может создать через прямой API заявку с `assessment=unavailable`: backend рассчитывает результат, но не отклоняет создание.
3. `need_info` умеет привязать существующие документы, но загрузки нового файла и изменения финансовых данных нет.
4. Ручное одобрение `manual_review` фактически запрещено: банк может запросить сведения или отказать, но не override policy.
5. Результат повторной оценки при банковском решении не сохраняется отдельным новым snapshot/check набором.
6. Нет Alembic; production startup использует `Base.metadata.create_all`.
7. Нет optimistic locking, idempotency key и надёжной защиты от конкурентных решений.
8. OpenAPI рекомендаций описывает старый вложенный формат ошибки, runtime возвращает плоский формат.
9. Auth вручную читается из Request, поэтому OpenAPI security scheme неполная.
10. `ready → disbursed` сейчас выполняет клиент; бизнес-решение аналитика отдельно не зафиксировано.

## Что сделал ML/DS-инженер

### Выполнено

- deterministic score 0–100 и risk level;
- объясняющие факторы с points/maxPoints;
- версии правил и признаков;
- аннуитет, покрытие, eligibility и альтернативная сумма;
- пять групп рекомендаций и два режима ранжирования;
- stress-сценарии падения выручки;
- строгий DTO рекомендаций;
- аудит входного snapshot и результата;
- 32 чистых unit-теста scoring/financing/ranking/stress;
- документация в `docs/ds_*`, `docs/financing_contract.md`, `docs/ranking_contract.md` и `docs/stress_contract.md`.

### Важно понимать

Это объяснимая rule-based система, а не обученная кредитная ML-модель. `eventProbability` всегда `null`, а score нельзя трактовать как вероятность дефолта.

### Частично или не выполнено

1. Нет target contract: события, горизонта, observation window, label source и leakage policy.
2. Нет исторического датасета и train/evaluate pipeline.
3. Нет predictive metrics, calibration, fairness и monitoring.
4. Нет model registry и связи версии с Git SHA/build artifact.
5. Нет полноценной model card с owner, governance и changelog.
6. Financial features не имеют `asOf`, периода, source и freshness SLA.
7. Stress доступен как Python-функция, но не опубликован через HTTP и не показан в UI.
8. Backend хранит `ScoringRule`, но расчёт использует константы кода — возможны две ложные «истины» policy.

## Что предоставил аналитик

В новых файлах нет отдельного финального аналитического артефакта, закрывающего ранее поставленные вопросы. Часть решений фактически закрепилась в коде:

- coverage threshold — `1.25`;
- low risk — score от `70`;
- итоговый оффер делает банк;
- `ready → disbursed` выполняет клиент;
- доступны approve/alternative/need_info/reject;
- alternative amount ищется по сетке 10 000 ₽.

Нужно либо официально подтвердить эти правила, либо изменить код. По-прежнему требуется data dictionary, контрольные расчётные примеры, политика manual review, состав сведений для `need_info`, владелец выдачи и формальное описание target для будущего ML.

## Что команда подключила на frontend

До дополнительного аудита уже были подключены:

- login/logout и восстановление `/me`;
- профиль компании и каталог;
- grouped recommendations;
- создание/чтение заявок;
- банковская очередь и решения;
- действия клиента;
- уведомления;
- backend WebSocket и polling fallback.

Frontend больше не использует `localStorage` или `sessionStorage` как источник бизнес-состояния.

## Что исправлено на frontend после аудита

1. API-клиент получил явные HTTP-методы, timeout, корректный `204`, проверку JSON, `ApiError.code` и `fieldErrors`.
2. Login/logout переведены на корректные POST без фиктивного `{}`.
3. Cookie-сессия синхронизируется между вкладками через `BroadcastChannel`.
4. При ошибке logout переход на `/login` больше не выполняется.
5. WebSocket использует reconnect с backoff и обрабатывает `4401`.
6. Полные realtime payload'ы заявки и уведомлений применяются локально без полного N+1 refresh на каждое событие.
7. После reconnect и возврата к видимой вкладке выполняется серверная синхронизация.
8. Recommendation adapter теперь сохраняет rate, assessment, recommendedAmount, evaluationId и rankingVersion.
9. UI показывает ставку конкретного offer, а не всегда ставку продукта.
10. Ввод суммы согласован с диапазоном создания заявки 50 000–5 000 000 ₽.
11. `need_info` получил форму комментария и выбор существующих документов вместо фиктивного подтверждения.
12. Банк может выполнить разрешённый backend переход `offer → rejected` как отзыв предложения.
13. Альтернативные условия проверяются на finite/диапазоны до запроса.
14. Nullable DTO уведомлений/заявок и статусы документов согласованы с backend.
15. Header получает название компании из серверного профиля.
16. Причина клиентского отказа берётся из последнего события, а не из старого позитивного комментария банка.
17. Неактивная компания больше не отображается как действующая.
18. Денежные значения с копейками больше не округляются принудительно до целого рубля.
19. После login восстанавливается исходный deep link.
20. В production `frontend/nginx.conf` добавлен proxy `/api/` и WebSocket Upgrade.
21. README приведён к server-backed архитектуре; старый relay обозначен как изолированная demo-инфраструктура.

## Критичная проблема текущего сервера

Проверка `http://31.77.79.88` 24 октября 2026 показала:

- `GET /` — `200`, frontend открывается;
- `GET /api/v1/health` — `200 text/html`, возвращается `index.html`;
- `GET /api/v1/credit-products` — `200 text/html`, возвращается `index.html`;
- `POST /api/v1/auth/login` — `405 Not Allowed` от Nginx.

Следовательно, на текущем стенде backend не проксируется через `/api/` либо ещё не развёрнут. Новая server-backed версия frontend на таком стенде не сможет войти и загрузить данные.

Для исправления нужно развернуть `docker compose up --build` либо применить Nginx-конфигурацию с `proxy_pass` на запущенный backend. После обновления `GET /api/v1/health` обязан возвращать JSON, а не HTML.

## Ошибки и риски, которые могут проявиться

### Критично до внешнего production

1. `POST /api/v1/demo/reset` публично удаляет demo-данные.
2. Default `AUTH_SECRET` известен, demo-пароли известны, cookie на HTTP не Secure.
3. FNS/BKI mock endpoint'ы публичны.
4. WebSocket не проверяет Origin.
5. Logout удаляет cookie, но не отзывает bearer token и уже открытые серверные сессии.
6. HTTPS/WSS на стенде отсутствуют.

### Функциональные

1. Изменения после клиентских переходов появятся в другой роли только через polling, пока backend не публикует все события.
2. В одном browser profile нельзя одновременно держать client и bank: HttpOnly-cookie общая. Нужны разные профили/инкогнито.
3. Очередь загружает детали N+1-запросами; при большом количестве заявок будет медленно.
4. Один проблемный detail endpoint всё ещё может ухудшить полное обновление очереди; `404` уже пропускается, остальные ошибки показываются пользователю.
5. Backend допускает nullable notification applicationId; системное уведомление можно прочитать, но переход к заявке не выполняется.
6. Нет загрузки новых документов, только выбор существующих.
7. Manual-review карточку можно отправить, но backend не разрешит банку одобрить её без устранения ограничений.
8. Realtime хранится в памяти одного процесса и не работает между несколькими workers без broker/pub-sub.
9. Publish WebSocket после commit может завершить HTTP ошибкой при гонке соединений.
10. Статусы документов `pending/rejected` могут приводить к `409 SOURCE_DATA_INVALID` вместо `need_info`.

## Остаток до полной картины

### P0 — поднять рабочий стенд

- развернуть backend и БД;
- включить `/api/` и WebSocket proxy;
- проверить login, health, Swagger и полный E2E на `31.77.79.88`;
- подключить домен, HTTPS/WSS и Secure cookie;
- заменить секреты и закрыть destructive demo endpoints.

### P1 — завершить функциональный MVP

- публиковать `application.updated` после каждой мутации;
- реализовать загрузку/обновление документов для `need_info`;
- решить и зафиксировать manual-review override;
- запретить создание `unavailable` заявки прямым API;
- сохранить повторную оценку при решении банка;
- добавить rich/batch list endpoint и убрать frontend N+1;
- унифицировать OpenAPI и runtime error schema;
- добавить миграции Alembic и проверить PostgreSQL;
- добавить idempotency и optimistic locking.

### P2 — ML и эксплуатация

- получить реальные labels и target contract;
- сделать train/evaluate pipeline только после появления валидных данных;
- добавить model/rule card, registry/version lineage и мониторинг;
- опубликовать stress API/UI, если он входит в демонстрацию;
- добавить frontend contract/E2E тесты;
- добавить WebSocket, CORS, security, concurrency и Docker integration tests.

## Проверка после frontend-исправлений

Успешно выполнены:

```text
npm run lint             — 0 warnings, 0 errors
npm run build            — production build успешен
npm run realtime:test    — broadcast passed
python -m pytest tests/test_scoring.py tests/test_financing.py tests/test_ranking.py tests/test_stress.py -q -p no:cacheprovider
                          — 32 passed
```

React Router обновлён внутри совместимой ветки с `6.28.0` до `6.30.6`, `@remix-run/router` — до `1.23.4`: три high-уязвимости устранены. `npm audit` оставляет две moderate-уязвимости, исправление которых требует отдельной миграции на React Router 7; SSR hydration в текущем SPA не используется, а восстановление deep link дополнительно запрещает `//` и обратный слеш.

Полный backend API suite локально повторно не запускался: на машине доступен Python 3.11 без SQLAlchemy, `uv` и Docker отсутствуют, а проект требует Python 3.12+. Команда ранее зафиксировала 52 прошедших теста в `docs/integration_status.md`, но внешний стенд пока не подтверждает рабочий API deployment.
