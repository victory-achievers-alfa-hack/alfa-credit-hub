# alfa-credit-hub
Личный кабинет для сегмента малого и микробизнеса с ИИ‑ассистентом, который понимает потребности клиента, помогает выбрать подходящий кредитный продукт и пройти весь путь от заявки до решения.

### Быстрый запуск | Quick start

**Backend:**
1. Скачать зависимости:
   ```bash
   uv sync
   ```
   
2. Запустить сервер:
* Документация API (Swagger): http://localhost:8000/docs
   ```bash
   uv run uvicorn backend.main:app --reload
   ```
   

**Frontend:**
   ```bash
    cd frontend
    npm install
    npm run dev
   ```