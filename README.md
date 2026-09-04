# HAVA VPN

MVP единой системы продажи VPN-доступа: Telegram-бот, Mini App, FastAPI backend, Telegram Stars, PostgreSQL, web-admin и сменный VPN provider.

## Что уже работает

- `/start`, меню, `/paysupport` и запуск Mini App;
- тарифы из БД и редактируемые admin API;
- Stars invoice → `pre_checkout_query` → идемпотентный `successful_payment`;
- раздельные состояния оплаты и provisioning;
- создание/продление одного VPN-профиля через `VpnProvider`;
- случайная subscription URL, отзыв и перевыпуск;
- локальная генерация QR API без сторонних сервисов;
- Mini App с экранами Главная, Тарифы, VPN и Профиль;
- базовый dashboard `/admin`, обращения поддержки и audit log;
- mock provider для разработки и Marzban adapter для продакшена.

## Локальный запуск

Требуется Python 3.9+ (для production используется Python 3.12 из Dockerfile).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Откройте `http://localhost:8000/health`. При локальном `PUBLIC_URL` бот сам запускается через long polling. Mini App авторизуется только внутри Telegram; это ожидаемое ограничение безопасности.

## Docker / PostgreSQL

```bash
docker compose up --build
```

Для Telegram Mini App нужен публичный HTTPS URL. Укажите его в `PUBLIC_URL`, настройте URL Mini App через BotFather и установите webhook:

```text
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://YOUR_DOMAIN/telegram/webhook/WEBHOOK_SECRET&secret_token=WEBHOOK_SECRET
```

Не вставляйте реальный токен в URL истории терминала. Для production лучше выполнить запрос через безопасный deployment secret.

## Подключение Marzban

В `.env`:

```dotenv
VPN_PROVIDER=marzban
MARZBAN_URL=https://panel.example.com
MARZBAN_USERNAME=...
MARZBAN_PASSWORD=...
```

Совместимость полей Marzban проверьте с версией вашей панели. Пока `VPN_PROVIDER=mock`, генерируется демонстрационная VLESS-строка и реальный VPN-трафик не поднимается.

## Важное перед production

1. Перевыпустите Telegram bot token в BotFather: текущий токен был опубликован в переписке.
2. Замените `ADMIN_TOKEN` и `WEBHOOK_SECRET` длинными случайными значениями.
3. Укажите HTTPS-домен, строгий `CORS_ORIGINS`, PostgreSQL и реальные credentials Marzban.
4. Поставьте reverse proxy, rate limiting, резервное копирование и worker для повторов provisioning/уведомлений.
5. Добавьте admin 2FA, юридические документы и мониторинг.

## Структура

```text
app/api/       REST и subscription endpoint
app/bot/       aiogram handlers и Stars
app/core/      настройки и проверка Telegram initData
app/db/        модели и async session
app/services/  пользователи и provisioning
app/vpn/       независимый Mock/Marzban adapter
app/static/    Mini App и базовая web-admin
tests/         проверки security primitives
```
