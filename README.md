# VPN Telegram Bot Platform

Полностью автоматизированный сервис VPN с оплатой через Telegram Stars, быстрым провиженом Amnezia/WireGuard/OpenVPN и SmartDNS. Репозиторий содержит минимально жизнеспособный стек для старта в одном `docker-compose.yml`.

## Возможности
- Тарифы: Trial (3 дня), Light, Family, Unlimited (+опционально выделенный IP), годовые подписки со скидкой 35%.
- Процессинг платежей через Telegram Stars (плейсхолдер API) и подготовка к крипто-эквайрингу.
- Автоматический триал, grace-period 3 дня с шейпингом 5–10 Мбит/с.
- Provisioner с шаблонами конфигов AmneziaWG/WireGuard/OpenVPN и генерацией QR.
- Реферальная программа и промокоды (структура заложена в Billing), напоминания о продлении по расписанию.
- SmartDNS на выделенном узле для YouTube/стриминга.
- Простая веб-панель для статусов и скачивания конфигов.

## Структура
- `bot/` — aiogram-бот с командой `/start` и точками интеграции с backend.
- `services/billing/` — FastAPI сервис тарифов, платежей и подписок.
- `services/provisioner/` — FastAPI сервис генерации конфигураций.
- `web/dashboard/` — веб-панель на FastAPI + Jinja2.
- `docs/` — архитектура и пошаговое развертывание.
- `scripts/` — бэкап БД в S3-совместимое хранилище.

## Быстрый старт
1. Скопируйте `.env.example` в `.env` и заполните токен бота и креды к БД/MinIO.
2. Запустите: `docker compose up -d --build`.
3. Проверка:
   - `curl http://localhost:8000/health` (billing)
   - `curl http://localhost:8001/health` (provisioner)
   - Откройте `http://localhost:8002` (dashboard)

Более детальная инструкция в `docs/deployment.md`.
