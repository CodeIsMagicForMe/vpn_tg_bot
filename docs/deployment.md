# Развертывание

Пошаговый план запуска минимально жизнеспособной версии.

## 1. Подготовка окружения
1. Установите Docker и Docker Compose v2.
2. Склонируйте репозиторий и перейдите в каталог проекта.
3. Скопируйте `.env.example` в `.env` и задайте реальные значения:
   ```bash
   cp .env.example .env
   # BOT_TOKEN, BOT_ADMIN_IDS, пароли к БД/MinIO
   ```

## 2. Локальный запуск через Docker Compose
```bash
docker compose pull
docker compose up -d --build
```
Сервисы и порты:
- Billing: `http://localhost:8000/health`
- Provisioner: `http://localhost:8001/health`
- Dashboard: `http://localhost:8002`
- Bot Webhook/health (polling внутри): `:8081`
- Postgres: `localhost:5432`
- MinIO: `http://localhost:9000` (консоль `:9001`)

## 3. Настройка внешних зависимостей
- **PostgreSQL**: для прод замените `POSTGRES_HOST/PORT` на данные Neon/Yandex Managed. Запустите миграции Alembic после появления схемы (плейсхолдер под будущие миграции в `scripts`).
- **Object Storage**: создайте bucket `configs` в Cloudflare R2/MinIO, пропишите `MINIO_ENDPOINT` и ключи.
- **Домены**: добавьте A/AAAA-записи на узлы NL и SmartDNS, настройте SNI-маскировку.
- **SmartDNS**: установите `unbound` + `3proxy/nginx` на отдельном VPS, пропишите адрес в конфигурации Provisioner при генерации конфигов.

## 4. Первичное тестирование флоу
1. Вызвать `/health` у всех сервисов.
2. Получить список тарифов: `curl http://localhost:8000/tariffs`.
3. Старт платежа: `curl -X POST http://localhost:8000/payments/start -H 'Content-Type: application/json' -d '{"user_id":1,"tariff_code":"light"}'`.
4. Подтвердить платеж: `curl -X POST http://localhost:8000/payments/<invoice_id>/confirm` и убедиться, что даты и grace-period возвращаются.
5. Провижн конфигурации: `curl -X POST http://localhost:8001/provision -H 'Content-Type: application/json' -d '{"user_id":1,"protocol":"wireguard","device_name":"macbook","tariff_code":"light"}'`.
6. Зайти в `http://localhost:8002` и убедиться, что тарифа и статусы отображаются.

## 5. Прод-профиль
- Перейдите на `systemd` юниты для Compose (`docker compose --profile prod up -d`).
- Включите Netdata на всех VPS и настройте алерты в Telegram.
- Настройте бэкапы: `pg_dump` + `rclone` -> R2/B2 (см. `scripts/backup.sh` шаблон).
- Добавьте HTTPS (Caddy/Traefik/nginx) перед Dashboard и API, настраивайте HSTS.
- Ограничьте доступ к MinIO/R2 через политики с TTL-ссылками.

## 6. Масштабирование
- Горизонтальное масштабирование Provisioner/Billing через replicas + общий Postgres/Redis.
- Выделенные провижен-узлы для Amnezia/WireGuard/OpenVPN с Ansible-ролями.
- Квоты: ограничение устройств и скорости (tc/cake-autorate) подключается через Provisioner API.

## 7. Дальшие шаги разработки
- Реализовать платежи Stars (invoices и webhooks) и крипто-эквайринг.
- Добавить Pydantic-модели в БД (SQLAlchemy) и Alembic миграции.
- Подключить nDPI light для автоблокировок торрентов.
- Внедрить реферальную систему, промокоды, ремаркетинг уведомления.
