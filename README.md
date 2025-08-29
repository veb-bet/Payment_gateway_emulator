# Payment_gateway_emulator
Эмулятор платежного шлюза на Python, который включает вебхуки, подписи, ретраи, идемпотентные ключи, очереди и дедупликацию.

---
## Запуск проекта

### Вариант 1: Локально (без Docker)

1. Установите зависимости:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Запустите Redis (например через Docker):
   ```bash
   docker run -p 6379:6379 -d redis:7
   ```

3. Запустите приложение:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. API будет доступен по адресу:
   - Swagger UI: http://127.0.0.1:8000/docs
   - OpenAPI JSON: http://127.0.0.1:8000/openapi.json

---
### Вариант 2: Docker Compose

1. Соберите и запустите контейнеры:
   ```bash
   docker-compose up --build
   ```

2. Приложение будет доступно на http://127.0.0.1:8000

---
## Примеры использования (curl)

1. **Регистрация мерчанта**
   ```bash
   curl -X POST "http://127.0.0.1:8000/admin/register_merchant" \
        -H "Content-Type: application/json" \
        -d '{"merchant_id":"m1","webhook_url":"http://host.docker.internal:8000/test/receive_webhook"}'
   ```


2. **Создание платежа (с идемпотентным ключом)**
   ```bash
   curl -X POST "http://127.0.0.1:8000/charge" \
        -H "Content-Type: application/json" \
        -H "Idempotency-Key: abc123" \
        -d '{"merchant_id":"m1","amount":1000}'
   ```


3. **Проверка статуса транзакции**
   ```bash
   curl http://127.0.0.1:8000/status/<tx_id>
   ```

4. **Приём вебхука (тестовый эндпоинт)**
   ```bash
   curl -X POST "http://127.0.0.1:8000/test/receive_webhook?secret=<секрет>" \
        -H "Content-Type: application/json" \
        -H "X-PG-Signature: <подпись>" \
        -d '{"tx_id":"123","status":"succeeded"}'
   ```
